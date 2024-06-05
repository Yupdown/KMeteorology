import datetime

from imgui.integrations.glfw import GlfwRenderer
from OpenGL.GL import *
import glm
import glfw

import imgui

import logging
import sys
import time

import mesh
import shader
import territory_parser
import weather_data
from aws_point import AWSPoint


radio_params = (
    ("TA", "기온"),
    ("HM", "습도"),
    ("WS10", "풍속"),
    ("PS", "기압"),
    ("RN-60m", "강수량")
)
selected_type = radio_params[0][0]

# set logging level
logging.basicConfig(level=logging.INFO)
scroll_y = 0.0

def impl_glfw_init():
    width, height = 1280, 960
    window_name = "KMeteorology - Weather Data Visualization"

    if not glfw.init():
        logging.error("Could not initialize OpenGL context")
        sys.exit(1)

    # OS X supports only forward-compatible core profiles from 3.2
    glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 3)
    glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 3)
    glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
    glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL_TRUE)
    glfw.window_hint(glfw.STENCIL_BITS, 8)

    # Enable Multi Sample Anti Aliasing
    glfw.window_hint(glfw.SAMPLES, 8)

    # Create a windowed mode window and its OpenGL context
    window = glfw.create_window(width, height, window_name, None, None)
    glfw.make_context_current(window)

    if not window:
        glfw.terminate()
        logging.error("Could not initialize Window")
        sys.exit(1)

    return window


def scroll_callback(window, xoffset, yoffset):
    global scroll_y
    scroll_y += yoffset
    scroll_y = max(0, min(15, scroll_y))


def gen_global_vbo():
    guid = glGenBuffers(1)
    glBindBuffer(GL_UNIFORM_BUFFER, guid)
    glBufferData(GL_UNIFORM_BUFFER, 128, None, GL_STATIC_DRAW)
    glBindBuffer(GL_UNIFORM_BUFFER, 0)
    glBindBufferBase(GL_UNIFORM_BUFFER, 0, guid)
    return guid


def create_quad():
    mesh_quad = mesh.Mesh()
    mesh_quad.vertices = [
        -1.0, -1.0, 0.0,
        1.0, -1.0, 0.0,
        1.0, 1.0, 0.0,
        -1.0, 1.0, 0.0
    ]
    mesh_quad.indices = [
        0, 1, 2,
        2, 3, 0
    ]
    mesh_quad.gen_buffer()
    return mesh_quad

texture = None
tw, th = 32, 32
fbo = None
rbo = None


def resize_render_target(width, height):
    global texture

    glBindTexture(GL_TEXTURE_2D, texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, tw, th, 0, GL_RGB, GL_UNSIGNED_BYTE, None)

    glBindRenderbuffer(GL_RENDERBUFFER, rbo)
    glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, tw, th)

    glBindTexture(GL_TEXTURE_2D, 0)
    glBindRenderbuffer(GL_RENDERBUFFER, 0)


def create_render_target(width, height):
    global texture, fbo, rbo

    fbo = glGenFramebuffers(1)
    glBindFramebuffer(GL_FRAMEBUFFER, fbo)

    texture = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, texture)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, width, height, 0, GL_RGB, GL_UNSIGNED_BYTE, None)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, texture, 0)

    rbo = glGenRenderbuffers(1)
    glBindRenderbuffer(GL_RENDERBUFFER, rbo)
    glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH24_STENCIL8, width, height)
    glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_STENCIL_ATTACHMENT, GL_RENDERBUFFER, rbo)

    if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
        logging.error("Framebuffer is not complete!")

    glBindFramebuffer(GL_FRAMEBUFFER, 0)
    glBindTexture(GL_TEXTURE_2D, 0)
    glBindRenderbuffer(GL_RENDERBUFFER, 0)


def window_resize_callback(window, width, height):
    global tw, th
    if height == 0:
        return

    aspect_ratio = width / height
    tw = int(32 * aspect_ratio)
    th = 32

    # resize the texture
    if texture:
        resize_render_target(tw, th)


def main():
    global window, selected_type
    window = impl_glfw_init()
    imgui.create_context()
    font_header = imgui.get_io().fonts.add_font_from_file_ttf("Resources/naru.ttf", 24, None, imgui.get_io().fonts.get_glyph_ranges_korean())
    font_body = imgui.get_io().fonts.add_font_from_file_ttf("Resources/naru.ttf", 16, None, imgui.get_io().fonts.get_glyph_ranges_korean())
    impl = GlfwRenderer(window)

    glfw.set_window_size_callback(window, window_resize_callback)
    glfw.set_scroll_callback(window, scroll_callback)

    info_file = open('aws_info.txt', 'r')
    points = {}
    for line in info_file:
        if line.startswith('#'):
            continue
        info = line.split()
        point = AWSPoint(info)
        points[point.id] = point
    weather_data.initialize()
    for p in points.values():
        p.initialize_data(weather_data)

    create_render_target(tw, th)
    shaders = dict()
    shaders["DEFAULT"] = shader.Shader("Resources/vertex_default.glsl", "Resources/fragment_default.glsl")
    shaders["TERRITORY"] = shader.Shader("Resources/vertex_territory.glsl", "Resources/fragment_territory.glsl")
    shaders["HEATMAP"] = shader.Shader("Resources/vertex_heatmap.glsl", "Resources/fragment_heatmap.glsl")

    for shader_program in shaders.values():
        shader_program.load_shaders()

    guid = gen_global_vbo()

    glEnable(GL_MULTISAMPLE)

    mouse_pos_current = (0, 0)
    mouse_pos_last = (0, 0)
    moust_pos_delta = (0, 0)
    mouse_pos_drag = (0, 0)
    current_scale = 1.0
    time_factor = 1.0

    camera_center = (-399, -379)
    camera_size = 400

    elapsed_time = time.time()

    territory_mesh = territory_parser.TerritoryMesh("Resources/territory.svg")
    quad_mesh = create_quad()

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

        new_time = time.time()
        delta_time = new_time - elapsed_time
        elapsed_time = new_time

        mouse_pos_last = mouse_pos_current
        mouse_pos_current = glfw.get_cursor_pos(window)

        if not imgui.get_io().want_capture_mouse:
            moust_pos_delta = (0, 0)
            if glfw.get_mouse_button(window, glfw.MOUSE_BUTTON_LEFT) == glfw.PRESS:
                moust_pos_delta = (
                    mouse_pos_current[0] - mouse_pos_last[0],
                    mouse_pos_current[1] - mouse_pos_last[1]
                )
                mouse_pos_drag = (
                    mouse_pos_drag[0] + moust_pos_delta[0],
                    mouse_pos_drag[1] + moust_pos_delta[1]
                )

        screen_size = glm.vec2(glfw.get_framebuffer_size(window))
        aspect_ratio = screen_size.x / screen_size.y if screen_size.y != 0.0 else 1.0

        if screen_size.y != 0.0:
            camera_center = (
                camera_center[0] + moust_pos_delta[0] * 2.0 * camera_size / screen_size.y,
                camera_center[1] + moust_pos_delta[1] * 2.0 * camera_size / screen_size.y
            )
        # clamp camera center
        camera_center = (
            max(-800, min(0, camera_center[0])),
            max(-760, min(0, camera_center[1]))
        )

        a = camera_size
        b = 400 * pow(2, scroll_y * -0.5)
        camera_size = a + (b - a) * delta_time * 16.0

        world_matrix = glm.scale(glm.mat4(1), glm.vec3(-1.0, -1.0, 1.0))

        view_matrix = glm.lookAt(glm.vec3(camera_center[0], camera_center[1], -1), glm.vec3(camera_center[0], camera_center[1], 0), glm.vec3(0, 1, 0))
        projection_matrix = glm.ortho(-aspect_ratio * camera_size, aspect_ratio * camera_size, -camera_size, camera_size, -1000.0, 1000.0)

        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        # update global uniform buffer
        glBindBuffer(GL_UNIFORM_BUFFER, guid)
        glBufferSubData(GL_UNIFORM_BUFFER, 0, 64, glm.value_ptr(view_matrix))
        glBufferSubData(GL_UNIFORM_BUFFER, 64, 64, glm.value_ptr(projection_matrix))
        glBindBuffer(GL_UNIFORM_BUFFER, 0)

        # First Pass
        glBindFramebuffer(GL_FRAMEBUFFER, fbo)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glViewport(0, 0, tw, th)

        shader_program = shaders["HEATMAP"]
        glUseProgram(shader_program.active_shader)

        glBindVertexArray(quad_mesh.vao)
        glDrawElements(GL_TRIANGLES, len(quad_mesh.indices), GL_UNSIGNED_INT, None)

        # Second Pass
        glBindFramebuffer(GL_FRAMEBUFFER, 0)
        glBindTexture(GL_TEXTURE_2D, texture)

        # color: #1F2025
        glClearColor(0.12, 0.12, 0.14, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)
        glViewport(0, 0, int(screen_size.x), int(screen_size.y))

        imgui.new_frame()
        imgui.push_font(font_body)

        shader_program = shaders["TERRITORY"]
        glUseProgram(shader_program.active_shader)

        model_location = glGetUniformLocation(shader_program.active_shader, "model_Transform")
        glUniformMatrix4fv(model_location, 1, GL_FALSE, glm.value_ptr(world_matrix))

        # model_location = glGetUniformLocation(shader_program.active_shader, "model_Color")
        # # color: #3F4045
        # glUniform4f(model_location, 0.25, 0.25, 0.27, 1.0)

        glBindVertexArray(territory_mesh.vao)
        glEnable(GL_STENCIL_TEST)

        glStencilFunc(GL_ALWAYS, 0, 1)
        glStencilOp(GL_INVERT, GL_INVERT, GL_INVERT)
        glColorMask(GL_FALSE, GL_FALSE, GL_FALSE, GL_FALSE)

        for p in territory_mesh.params:
            glDrawElements(GL_TRIANGLE_FAN, p[1], GL_UNSIGNED_INT, ctypes.c_void_p(p[0] * 4))

        glStencilFunc(GL_EQUAL, 1, 1)
        glStencilOp(GL_KEEP, GL_KEEP, GL_KEEP)
        glColorMask(GL_TRUE, GL_TRUE, GL_TRUE, GL_TRUE)

        for p in territory_mesh.params:
            glDrawElements(GL_TRIANGLE_FAN, p[1], GL_UNSIGNED_INT, ctypes.c_void_p(p[0] * 4))

        shader_program = shaders["DEFAULT"]
        glUseProgram(shader_program.active_shader)
        glDisable(GL_STENCIL_TEST)

        model_location = glGetUniformLocation(shader_program.active_shader, "model_Transform")
        glUniformMatrix4fv(model_location, 1, GL_FALSE, glm.value_ptr(world_matrix))

        model_location = glGetUniformLocation(shader_program.active_shader, "model_Color")
        glUniform4f(model_location, 0.75, 0.75, 0.8, 1.0)

        for p in territory_mesh.params:
            glDrawElements(GL_LINE_LOOP, p[1], GL_UNSIGNED_INT, ctypes.c_void_p(p[0] * 4))

        glBindVertexArray(quad_mesh.vao)

        viewproj_matrix = projection_matrix * view_matrix

        for p in points.values():
            inverse_scale = camera_size * 0.005
            model_matrix = glm.translate(glm.mat4(1), glm.vec3(-p.x, -p.y, 0))
            model_matrix = glm.scale(model_matrix, glm.vec3(inverse_scale, inverse_scale, inverse_scale))

            point_active = p.id in weather_data.data_hoursofday[23]
            point_type = p.code[0] == '4'

            model_location = glGetUniformLocation(shader_program.active_shader, "model_Color")
            if point_active:
                if point_type:
                    glUniform4f(model_location, 0.3, 0.98, 0.18, 1.0)
                else:
                    glUniform4f(model_location, 0.0, 0.3, 0.9, 1.0)
            else:
                glUniform4f(model_location, 0.8, 0.0, 0.0, 1.0)
            model_location = glGetUniformLocation(shader_program.active_shader, "model_Transform")
            glUniformMatrix4fv(model_location, 1, GL_FALSE, glm.value_ptr(model_matrix))

            glDrawElements(GL_TRIANGLES, len(quad_mesh.indices), GL_UNSIGNED_INT, None)

            if scroll_y < 4 or (scroll_y < 8 and not point_type):
                p.reset_imgui()
                continue

            # draw text of the point (every new window)
            p.draw_imgui(viewproj_matrix, screen_size, delta_time)

        imgui.pop_font()
        imgui.push_font(font_header)

        # Show the Title of the Application (font size: 24)
        imgui.set_next_window_position(4, 4)
        imgui.begin("Title", False, imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_ALWAYS_AUTO_RESIZE)
        imgui.text("KMeteorology - AWS 기상 자료 시각화")

        imgui.pop_font()
        imgui.push_font(font_body)

        # Show the current time
        time_str = weather_data.time_criteria.strftime("%Y-%m-%d %H:%M")
        imgui.separator()
        imgui.text("기준 시간: %s" % time_str)
        imgui.end()

        # Show the AWS Information (font size: 16)
        content_size = (400, 320)
        imgui.set_next_window_position(screen_size.x - 4 - content_size[0], screen_size.y - 4 - content_size[1])
        imgui.set_next_window_size(content_size[0], content_size[1])
        imgui.begin("AWS Information", False, imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE)
        imgui.text("AWS 그래프 자료")

        imgui.spacing()
        imgui.spacing()
        imgui.spacing()

        imgui.separator()
        imgui.text('Control')
        imgui.spacing()
        imgui.spacing()
        time_factor = imgui.slider_float('Time Factor', time_factor, 0, 1, '')[1]
        hours_delta = 24 * (1 - time_factor)
        lerped_time = weather_data.time_criteria - datetime.timedelta(hours=hours_delta)
        imgui.text('Time: %s' % lerped_time.strftime('%Y-%m-%d %H:%M'))

        imgui.spacing()
        imgui.spacing()
        imgui.spacing()

        imgui.separator()
        imgui.text('Mode')
        imgui.spacing()
        imgui.spacing()
        for param in radio_params:
            clicked = imgui.radio_button(f'{param[0]} : {param[1]}', selected_type == param[0])
            if clicked:
                selected_type = param[0]
        imgui.end()

        imgui.pop_font()
        imgui.render()
        impl.render(imgui.get_draw_data())
        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


if __name__ == "__main__":
    main()
