from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image
import glfw
from ctypes import c_void_p

import numpy as np
from fealpy import logger
import ipdb

from gl_mesh import GLMesh
from coordinate_axes import CoordinateAxes
from kernel import calculate_rotation_matrix
import os


class OpenGLPlotter:
    def __init__(self, width=800, height=600, title="OpenGL Application"):
        """
        @brief 
        """
        if not glfw.init():
            raise Exception("GLFW cannot be initialized!")

        self.dragging = False
        self.last_mouse_pos = (width / 2, height / 2)
        self.first_mouse_use = True
        self.meshes = []
        self.texture_unit = 0 # 纹理单元计数器

        self.view_angle = 0 # 0 代表 X 轴，1 代表 Y 轴， 2 代表 Z 轴
        self.mode = 2  # 默认同时显示边和面
        self.faceColor = (0.5, 0.7, 0.9, 1.0)  # 浅蓝色
        self.edgeColor = (1.0, 1.0, 1.0, 1.0)  # 白色
        self.bgColor = (0.1, 0.2, 0.3, 1.0)   # 深海军蓝色背景

        self.transform = np.identity(4, dtype=np.float32)

        self.zNear = 0.1  # 近平面
        self.zFar = 100.0  # 远平面

        
        self.window = glfw.create_window(width, height, title, None, None)
        if not self.window:
            glfw.terminate()
            raise Exception("GLFW window cannot be created!")
        
        glfw.make_context_current(self.window)
        # 启用深度测试
        glEnable(GL_DEPTH_TEST)
        #glEnable(GL_CULL_FACE);
        #glFrontFace(GL_CCW);

        # 设置视口大小
        glViewport(0, 0, width, height)

        # 顶点着色器源码
        self.general_vertex_shader_source = """
        #version 460 core
        layout (location = 0) in vec3 aPos;
        layout (location = 1) in vec2 aTexCoords;
        uniform mat4 transform; //变换矩阵

        out vec2 TexCoords;

        void main()
        {
            gl_Position = transform * vec4(aPos.x, -aPos.y, aPos.z, 1.0);
            //gl_Position = projection * transform * vec4(aPos, 1.0);
            TexCoords = aTexCoords;
        }
        """

        # 片段着色器源码
        self.general_fragment_shader_source = """
        #version 460 core
        in vec2 TexCoords;

        uniform int mode;  // 0: 显示面 1: 显示边 2: 显示面和边 3: 如果有纹理数据显示纹理
        uniform vec4 faceColor;
        uniform vec4 edgeColor;
        uniform sampler2D textureSampler0;
        out vec4 FragColor;

        void main()
        {
            if (mode == 0) {
                FragColor = faceColor;  // 只显示面
            } else if (mode == 1) {
                FragColor = edgeColor;  // 只显示边
            } else if (mode == 2) {
                FragColor = faceColor;  // 同时显示面和边
            } else if (mode == 3) {
                FragColor = texture(textureSampler0, TexCoords); // 使用纹理
            }
        }
        """

        self.mix_vertex_shader_source = """
        #version 460 core
        layout (location = 0) in vec3 aPos;
        layout (location = 1) in vec2 auv0;
        layout (location = 2) in vec2 auv1;
        layout (location = 3) in float aWeight;
        uniform mat4 transform; // 变换矩阵

        out vec2 uv0;
        out vec2 uv1;
        out float Weight;

        void main()
        {
            gl_Position = transform * vec4(aPos.x, -aPos.y, aPos.z, 1.0);
            uv0 = auv0;
            uv1 = auv1;
            Weight = aWeight;
        }
        """

        self.mix_fragment_shader_source = """
        #version 460 core
        in vec2 uv0;
        in vec2 uv1;
        in float Weight;

        uniform int mode;  // 0: 显示面 1: 显示边 2: 显示面和边 3: 如果有纹理数据显示纹理
        uniform vec4 faceColor;
        uniform vec4 edgeColor;
        uniform sampler2D textureSampler0;
        uniform sampler2D textureSampler1;

        out vec4 FragColor;

        void main()
        {

            if (mode == 0) {
                FragColor = faceColor;  // 只显示面
            } else if (mode == 1) {
                FragColor = edgeColor;  // 只显示边
            } else if (mode == 2) {
                FragColor = faceColor;  // 同时显示面和边
            } else if (mode == 3) {
                vec4 color1 = texture(textureSampler0, uv0);
                vec4 color2 = texture(textureSampler1, uv1);
                FragColor = mix(color1, color2, Weight);
                //FragColor = Weight * color1 + (1.0 - Weight) * color2;
                //FragColor = color1;
                //FragColor = color2;
            }
        }
        """

        # 编译着色器
        self.general_shader_program = self.create_shader_program(self.general_vertex_shader_source, self.general_fragment_shader_source)
        self.mix_shader_program = self.create_shader_program(self.mix_vertex_shader_source, self.mix_fragment_shader_source)

        loc = glGetUniformLocation(self.mix_shader_program, "textureSampler0")
        print("loc0 : ", loc)
        loc = glGetUniformLocation(self.mix_shader_program, "textureSampler1")
        print("loc1 : ", loc)


        # 设置鼠标键盘回调函数
        glfw.set_key_callback(self.window, self.key_callback)
        glfw.set_cursor_pos_callback(self.window, self.mouse_callback)
        glfw.set_mouse_button_callback(self.window, self.mouse_button_callback)
        glfw.set_scroll_callback(self.window, self.scroll_callback)
        glfw.set_window_size_callback(self.window, self.window_resize_callback)

        self.update_projection_matrix(width, height)
        self.coordinate_axes = CoordinateAxes()
        logger.info(f"Initialized the OpenGLPloter Object!" )

    def update_projection_matrix(self, width, height):
        """
        """
        aspect_ratio = width / height
        fov = np.radians(45)  # Field of view, 45 degrees
        near = 0.1  # Near clipping plane
        far = 100.0  # Far clipping plane

        # Create a perspective projection matrix
        self.projection = np.zeros((4, 4), dtype=np.float32)
        self.projection[0, 0] = 1 / (aspect_ratio * np.tan(fov / 2))
        self.projection[1, 1] = 1 / np.tan(fov / 2)
        self.projection[2, 2] = -(far + near) / (far - near)
        self.projection[2, 3] = -(2 * far * near) / (far - near)

        self.projection[3, 2] = -1

    def add_mesh(self, node, cell=None, texture_paths=[], flip='LR', 
                 texture_folders = []):
        logger.info(f"Add GLMesh with {len(node)} nodes!")
        if len(texture_paths) < 2:
            self.meshes.append(GLMesh(node, 
                cell=cell, 
                texture_paths=texture_paths,
                texture_folders=texture_folders,
                texture_unit=self.texture_unit, flip=flip, 
                shader_program=self.general_shader_program))
        else:
            self.meshes.append(GLMesh(node, 
                cell=cell, 
                texture_paths=texture_paths,
                texture_folders=texture_folders,
                texture_unit=self.texture_unit, flip=flip, 
                shader_program=self.mix_shader_program))
        self.texture_unit += len(texture_paths)

    def compile_shader(self, source, shader_type):
        shader = glCreateShader(shader_type)
        glShaderSource(shader, source)
        glCompileShader(shader)
        if glGetShaderiv(shader, GL_COMPILE_STATUS) != GL_TRUE:
            error = glGetShaderInfoLog(shader).decode('utf-8')
            raise Exception(f"Shader compile failure: {error}")
        return shader

    def create_shader_program(self, vertex_shader_source, fragment_shader_source):
        """
        @brief 创建着色程序
        """
        vertex_shader = self.compile_shader(vertex_shader_source, GL_VERTEX_SHADER)
        fragment_shader = self.compile_shader(fragment_shader_source, GL_FRAGMENT_SHADER)
        shader_program = glCreateProgram()
        glAttachShader(shader_program, vertex_shader)
        glAttachShader(shader_program, fragment_shader)
        glLinkProgram(shader_program)
        if glGetProgramiv(shader_program, GL_LINK_STATUS) != GL_TRUE:
            error = glGetProgramInfoLog(shader_program).decode('utf-8')
            raise Exception(f"Program link failure: {error}")

        glDeleteShader(vertex_shader)
        glDeleteShader(fragment_shader)

        return shader_program

    def _bind_uinform(self, shader_program):
        """
        @brief 绑定uniform变量
        """
        # 使用着色器程序
        glUseProgram(shader_program)

        # 更新着色器的uniform变量
        glUniform4fv(glGetUniformLocation(shader_program, "faceColor"), 1, self.faceColor)
        glUniform4fv(glGetUniformLocation(shader_program, "edgeColor"), 1, self.edgeColor)

        # 应用变换
        transform_location = glGetUniformLocation(shader_program, "transform")

        if transform_location != -1:
            glUniformMatrix4fv(transform_location, 1, GL_FALSE, self.transform)
        else:
            logger.error("Transform location is invalid.")

    def save_screenshot(self, file_path):
        """
        @brief 保存屏幕截图
        """
        # 获取窗口的宽度和高度
        width, height = glfw.get_framebuffer_size(self.window)

        # 创建一个空的 numpy 数组来存储图像数据
        data = glReadPixels(0, 0, width, height, GL_RGB, GL_UNSIGNED_BYTE)

        # 将数据转为 numpy 数组并调整颜色通道的顺序（OpenGL 默认是从下到上，PIL 默认从上到下）
        img_data = np.frombuffer(data, dtype=np.uint8).reshape(height, width, 3)

        # Flip the image vertically because OpenGL stores images bottom to top
        img_data = np.flipud(img_data)

        # 使用 PIL 保存图片
        image = Image.fromarray(img_data)
        image.save(file_path)

    def run_pic(self):
        """
        @brief 
        """
        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            
            # 清除颜色缓冲区和深度缓冲区
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glClearColor(*self.bgColor)

            self._bind_uinform(self.mix_shader_program)
            self._bind_uinform(self.general_shader_program)

            # 只显示背面
            glEnable(GL_CULL_FACE)
            glCullFace(GL_BACK)
            #glCullFace(GL_FRONT)

            for mesh in self.meshes:
                mesh.draw(self.mode)

            # 关闭深度测试，确保坐标轴总是绘制在最前面
            # glDisable(GL_DEPTH_TEST)

            # 渲染坐标轴
            # self.coordinate_axes.render(self.projection, view_for_axes, np.identity(4))

            # 重新启用深度测试
            # glEnable(GL_DEPTH_TEST)

            glfw.swap_buffers(self.window)

        glfw.terminate()


    def run(self):
        """
        @brief 
        """
        allfolder = [] # 所有的纹理文件夹
        for mesh in self.meshes:
            allfolder = allfolder + mesh.texture_folders # 添加每个mesh的纹理文件夹
        allfolder = list(set(allfolder)) # 去重

        namemap = {allfolder[i]:i for i in range(len(allfolder))} # 文件夹名字到索引的映射

        allimgs = [] # 所有的纹理图片数据
        for folder in allfolder:
            allimgs.append(self.meshes[0].get_folder_textures(folder)) # 获取每个文件夹的纹理图片数据

        L = min([len(textures) for textures in allimgs]) # 所有纹理图片数据的最小长度
        frame_count = 0
        while not glfw.window_should_close(self.window):
            glfw.poll_events()
            
            # 清除颜色缓冲区和深度缓冲区
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glClearColor(*self.bgColor)

            self._bind_uinform(self.mix_shader_program)
            self._bind_uinform(self.general_shader_program)

            # 只显示背面
            glEnable(GL_CULL_FACE)
            glCullFace(GL_BACK)
            #glCullFace(GL_FRONT)

            #for mesh in self.meshes:
            #    mesh.draw(self.mode)
            for mesh in self.meshes:
                meshimg = [allimgs[namemap[folder]][frame_count] for folder in mesh.texture_folders]
                mesh.redraw(self.mode, meshimg)
            frame_count = (frame_count + 1) % L

            screenshot_path = f"screenshots/frame_{frame_count:04d}.png"  # 以帧编号命名
            self.save_screenshot(screenshot_path)
                

            # 关闭深度测试，确保坐标轴总是绘制在最前面
            # glDisable(GL_DEPTH_TEST)

            # 渲染坐标轴
            # self.coordinate_axes.render(self.projection, view_for_axes, np.identity(4))

            # 重新启用深度测试
            # glEnable(GL_DEPTH_TEST)

            glfw.swap_buffers(self.window)

        glfw.terminate()

    def key_callback(self, window, key, scancode, action, mods):
        if key == glfw.KEY_ESCAPE and action == glfw.PRESS:
            glfw.set_window_should_close(window, True)

        translate_speed = 0.1
        scale_factor = 1.1
        if action == glfw.PRESS or action == glfw.REPEAT:
            if key == glfw.KEY_UP:  # 向上平移
                self.transform[3, 1] += translate_speed
            elif key == glfw.KEY_DOWN:  # 向下平移
                self.transform[3, 1] -= translate_speed
            elif key == glfw.KEY_RIGHT:  # 向右平移
                self.transform[3, 0] += translate_speed
            elif key == glfw.KEY_LEFT:  # 向左平移
                self.transform[3, 0] -= translate_speed
            elif key == glfw.KEY_M:  # 假设我们使用 M 键来切换模式
                self.mode += 1
                if self.mode > 3:  # 超出范围后重置为 0
                    self.mode = 0
                logger.info(f"Update mode as {self.mode}")
            elif key == glfw.KEY_Z:  # 放大
                self.transform[:3, :3] *= scale_factor
            elif key == glfw.KEY_X:  # 缩小
                self.transform[:3, :3] /= scale_factor
            elif key == glfw.KEY_V:
                self.view_angle = (self.view_angle + 1) % 3  # 在0, 1, 2之间循环
                if self.view_angle == 0:  # X轴视角
                    self.transform = np.array([[0, 0, -1, 0],
                                               [0, 1, 0, 0],
                                               [1, 0, 0, 0],
                                               [0, 0, 0, 1]], dtype=np.float32)
                elif self.view_angle == 1:  # Y轴视角
                    self.transform = np.array([[1, 0, 0, 0],
                                               [0, 0, 1, 0],
                                               [0, -1, 0, 0],
                                               [0, 0, 0, 1]], dtype=np.float32)
                elif self.view_angle == 2:  # Z轴视角
                    self.transform = np.identity(4, dtype=np.float32)  # 默认视角


    def mouse_button_callback(self, window, button, action, mods):
        """
        """
        if button == glfw.MOUSE_BUTTON_LEFT:
            if action == glfw.PRESS:
                self.dragging = True
                self.first_mouse_use = True
            elif action == glfw.RELEASE:
                self.dragging = False

    def mouse_callback(self, window, xpos, ypos):
        if self.dragging:
            if self.first_mouse_use:
                self.last_mouse_pos = (xpos, ypos)
                self.first_mouse_use = False
                return

            # TODO
            yoffset = xpos - self.last_mouse_pos[0]
            xoffset = self.last_mouse_pos[1] - ypos
            self.last_mouse_pos = (xpos, ypos)

            if xoffset == 0 and yoffset == 0:
                return

            # 计算旋转矩阵，这里仅提供概念代码，具体实现需要根据虚拟轨迹球的逻辑来完成
            rotation_matrix = calculate_rotation_matrix(xoffset, yoffset)
            self.transform = np.dot(rotation_matrix, self.transform)

    def mouse_callback_old(self, window, xpos, ypos):
        print(f"Mouse position: {xpos}, {ypos}")
        if self.first_mouse_use:
            self.last_mouse_pos = (xpos, ypos)
            self.first_mouse_use = False

        xoffset = xpos - self.last_mouse_pos[0]
        yoffset = self.last_mouse_pos[1] - ypos  # 注意这里的y方向与屏幕坐标系相反
        self.last_mouse_pos = (xpos, ypos)

        sensitivity = 0.1
        xoffset *= sensitivity
        yoffset *= sensitivity

        # 生成旋转矩阵
        # 这里简化处理，只根据xoffset和yoffset来做基本的旋转，实际应用中可能需要更复杂的旋转逻辑
        rotation_x = np.array([[1, 0, 0, 0],
                               [0, np.cos(yoffset), -np.sin(yoffset), 0],
                               [0, np.sin(yoffset), np.cos(yoffset), 0],
                               [0, 0, 0, 1]], dtype=np.float32)

        rotation_y = np.array([[np.cos(xoffset), 0, np.sin(xoffset), 0],
                               [0, 1, 0, 0],
                               [-np.sin(xoffset), 0, np.cos(xoffset), 0],
                               [0, 0, 0, 1]], dtype=np.float32)

        self.transform = np.dot(self.transform, rotation_x)
        self.transform = np.dot(self.transform, rotation_y)

        logger.debug("Rotating: X offset {}, Y offset {}".format(xoffset, yoffset))

    def scroll_callback(self, window, xoffset, yoffset):
        """鼠标滚轮回调函数，用于缩放视图。"""
        scale_factor = 1.1  # 缩放系数
        if yoffset < 0:  # 向下滚动，缩小
            scale_factor = 1.0 / scale_factor
        # 更新变换矩阵
        self.transform[:3, :3] *= scale_factor

        fovy = 45.0  # 视场角 (度)
        width, height = glfw.get_framebuffer_size(window)
        aspect = width / height  # 宽高比 

        # 更新透视投影的近平面和远平面，避免裁剪
        self.zNear = max(0.1, self.zNear * scale_factor)  # 防止 zNear 变为负数或零
        self.zFar = self.zFar * scale_factor

        # 更新投影矩阵
        gluPerspective(fovy, aspect, self.zNear, self.zFar)


        logger.debug("Zooming: {}".format("In" if scale_factor > 1 else "Out"))


    def window_resize_callback(self, window, width, height):
        glViewport(0, 0, width, height)
        self.update_projection_matrix(width, height)
