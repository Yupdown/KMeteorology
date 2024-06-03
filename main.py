import requests  # requests 모듈 임포트
import time  # time 모듈 임포트

from imgui.integrations.glfw import GlfwRenderer
from OpenGL.GL import *
import glm
import glfw

import imgui

import logging
import sys

import mesh
import shader
import territory_parser
import util

# def download_file(file_url, save_path):
#     with open(save_path, 'wb') as f: # 저장할 파일을 바이너리 쓰기 모드로 열기
#         response = requests.get(file_url) # 파일 URL에 GET 요청 보내기
#         f.write(response.content) # 응답의 내용을 파일에 쓰기
#
# url = f'https://apihub.kma.go.kr/api/typ01/cgi-bin/url/nph-aws2_min?stn=0&disp=1&help=1&authKey=Ud0jPfajTAWdIz32o5wFcg'
# save_file_path = 'output_file.txt'
#
# # 파일 다운로드 함수를 호출합니다.
# download_file(url, save_file_path)


# set logging level
logging.basicConfig(level=logging.INFO)


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


def main():
    global window
    window = impl_glfw_init()
    imgui.create_context()
    impl = GlfwRenderer(window)

    info_file = open('aws_info.txt', 'r')
    coordinates = []
    for line in info_file:
        if line.startswith('#'):
            continue
        info = line.split()
        coordinates.append(util.convert_coordinate(float(info[1]), float(info[2])))

    shaders = dict()
    shaders["DEFAULT"] = shader.Shader("Resources/vertex_default.glsl", "Resources/fragment_default.glsl")

    for shader_program in shaders.values():
        shader_program.load_shaders()

    guid = gen_global_vbo()

    glEnable(GL_MULTISAMPLE)
    glEnable(GL_DEPTH_TEST)

    mouse_pos_current = (0, 0)
    mouse_pos_last = (0, 0)
    mouse_pos_drag = (-399, -379)
    mouse_scroll_integral = -10
    current_scale = 1.0

    territory_mesh = territory_parser.TerritoryMesh("Resources/territory.svg")
    quad_mesh = create_quad()

    while not glfw.window_should_close(window):
        glfw.poll_events()
        impl.process_inputs()

        io = imgui.get_io()
        mouse_pos_last = mouse_pos_current
        mouse_pos_current = io.mouse_pos.x, io.mouse_pos.y

        # if mouse is not captured by imgui, we can drag the model.
        if not io.want_capture_mouse:
            if io.mouse_down[0]:
                mouse_pos_drag = (
                    mouse_pos_drag[0] + mouse_pos_current[0] - mouse_pos_last[0],
                    mouse_pos_drag[1] + mouse_pos_current[1] - mouse_pos_last[1])
            mouse_scroll_integral += io.mouse_wheel
            mouse_scroll_integral = max(-10, min(10, mouse_scroll_integral))

        screen_size = io.display_size
        aspect_ratio = screen_size.x / screen_size.y if screen_size.y != 0.0 else 1.0

        # color: #1F2025
        glClearColor(0.12, 0.12, 0.14, 1.0)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT | GL_STENCIL_BUFFER_BIT)
        glViewport(0, 0, int(screen_size.x), int(screen_size.y))

        imgui.new_frame()

        scale_factor = 200 - mouse_scroll_integral * 19

        world_matrix = glm.scale(glm.mat4(1), glm.vec3(-1.0, -1.0, 1.0))

        view_matrix = glm.lookAt(glm.vec3(mouse_pos_drag[0], mouse_pos_drag[1], -1), glm.vec3(mouse_pos_drag[0], mouse_pos_drag[1], 0), glm.vec3(0, 1, 0))
        projection_matrix = glm.ortho(-aspect_ratio * scale_factor, aspect_ratio * scale_factor, -scale_factor, scale_factor, -1000.0, 1000.0)

        # update global uniform buffer
        glBindBuffer(GL_UNIFORM_BUFFER, guid)
        glBufferSubData(GL_UNIFORM_BUFFER, 0, 64, glm.value_ptr(view_matrix))
        glBufferSubData(GL_UNIFORM_BUFFER, 64, 64, glm.value_ptr(projection_matrix))
        glBindBuffer(GL_UNIFORM_BUFFER, 0)

        glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)

        shader_program = shaders["DEFAULT"]

        glUseProgram(shader_program.active_shader)

        model_location = glGetUniformLocation(shader_program.active_shader, "model_Transform")
        glUniformMatrix4fv(model_location, 1, GL_FALSE, glm.value_ptr(world_matrix))

        model_location = glGetUniformLocation(shader_program.active_shader, "model_Color")
        # color: #3F4045
        glUniform4f(model_location, 0.25, 0.25, 0.27, 1.0)

        glBindVertexArray(territory_mesh.vao)

        glEnable(GL_STENCIL_TEST)
        glDisable(GL_DEPTH_TEST)

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

        glDisable(GL_STENCIL_TEST)

        glUniform4f(model_location, 0.75, 0.75, 0.8, 1.0)
        for p in territory_mesh.params:
            glDrawElements(GL_LINE_LOOP, p[1], GL_UNSIGNED_INT, ctypes.c_void_p(p[0] * 4))

        glBindVertexArray(quad_mesh.vao)

        model_location = glGetUniformLocation(shader_program.active_shader, "model_Color")
        glUniform4f(model_location, 0.0, 1.0, 0.0, 1.0)
        model_location = glGetUniformLocation(shader_program.active_shader, "model_Transform")

        for p in coordinates:
            inverse_scale = scale_factor * 0.005
            model_matrix = glm.translate(glm.mat4(1), glm.vec3(-p[0], -p[1], 0))
            model_matrix = glm.scale(model_matrix, glm.vec3(inverse_scale, inverse_scale, inverse_scale))
            glUniformMatrix4fv(model_location, 1, GL_FALSE, glm.value_ptr(model_matrix))
            glDrawElements(GL_TRIANGLES, len(quad_mesh.indices), GL_UNSIGNED_INT, None)

        glEnable(GL_DEPTH_TEST)

        imgui.render()
        impl.render(imgui.get_draw_data())

        glfw.swap_buffers(window)

    impl.shutdown()
    glfw.terminate()


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


if __name__ == "__main__":
    main()