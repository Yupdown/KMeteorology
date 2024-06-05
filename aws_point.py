from array import array
import imgui
import imgui.core
import util
import weather_data
import glm


class AWSPoint:
    def __init__(self, point_info):
        self.id = point_info[0]
        self.x, self.y = util.transform_coordinate(float(point_info[1]), float(point_info[2]))
        self.name = point_info[8]
        self.code = point_info[3]
        self.array_data = {}
        self.has_data = False
        self.w = 0

    def initialize_data(self, weather_data):
        if self.id not in weather_data.data_hoursofday[0]:
            return
        for key in weather_data.keys:
            # float conversiable ?
            if key in ['YYMMDDHHMI', 'STN']:
                continue
            self.array_data[key] = array('f', [weather_data.data_hoursofday[i][self.id][key] for i in range(24)])
        self.has_data = True

    def draw_opengl(self, shader, viewproj_matrix):
        pass

    def reset_imgui(self):
        self.w = 0

    def draw_imgui(self, viewproj_matrix, screen_size, delta_time):
        v = viewproj_matrix * glm.vec3(-self.x, -self.y, 0)
        if v.x < -1 or v.x > 1 or v.y < -1 or v.y > 1:
            self.reset_imgui()
            return
        sv = glm.vec2((v.x + 1) * screen_size.x / 2 + 4, (-v.y + 1) * screen_size.y / 2)
        self.w = self.w + (200 - self.w) * delta_time * 10

        imgui.set_next_window_position(sv.x, sv.y)
        imgui.set_next_window_size(self.w, 210)
        imgui.begin(self.id, False, imgui.WINDOW_NO_TITLE_BAR | imgui.WINDOW_NO_RESIZE | imgui.WINDOW_NO_MOVE | imgui.WINDOW_NO_COLLAPSE | imgui.WINDOW_NO_BRING_TO_FRONT_ON_FOCUS | imgui.WINDOW_NO_MOUSE_INPUTS)
        imgui.text(f'[{self.id}] {self.name}')
        imgui.separator()
        plot_size = (max(self.w - 120, 10), 30)
        if self.has_data:
            direction = util.get_direction(self.array_data['WD10'][-1])
            imgui.plot_lines("%.1f°C" % self.array_data['TA'][-1], self.array_data['TA'], graph_size=plot_size)
            imgui.plot_histogram("%.1fmm" % self.array_data['RN-DAY'][-1], self.array_data['RN-60m'], scale_min=0, scale_max=40, graph_size=plot_size)
            imgui.plot_lines("%.1f%%" % self.array_data['HM'][-1], self.array_data['HM'], scale_min=0, scale_max=100, graph_size=plot_size)
            imgui.plot_lines("%.1fm/s (%s)" % (self.array_data['WS10'][-1], direction), self.array_data['WS10'], scale_min=0, scale_max=10, graph_size=plot_size)
            imgui.plot_lines("%.1fhPa" % self.array_data['PS'][-1], self.array_data['PS'], graph_size=plot_size)
        else:
            imgui.text("No Data")

        imgui.end()