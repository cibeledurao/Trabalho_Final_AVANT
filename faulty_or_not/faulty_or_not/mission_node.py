#!/usr/bin/env python3
import os
import subprocess
import rclpy
from rclpy.node import Node
from std_msgs.msg import String, Bool
from mavros_msgs.srv import CommandLong
from ament_index_python.packages import get_package_share_directory

class MissionNode(Node):
    def __init__(self):
        super().__init__('mission_node')

        self.declare_parameter('order_ascending', True)
        self.declare_parameter('relay_id', 0)

        self.order_ascending = self.get_parameter('order_ascending').get_parameter_value().bool_value
        self.relay_id = self.get_parameter('relay_id').get_parameter_value().integer_value

        self.figure_sub = self.create_subscription(String, '/detected_figure', self.figure_callback, 10)
        self.done_pub = self.create_publisher(Bool, '/mission/done', 10)
        self.audio_seq_pub = self.create_publisher(String, '/audio_sequence', 10)

        self.relay_client = self.create_client(CommandLong, '/mavros/cmd/command')

        self.figures = {}
        self.mission_completed = False

        try:
            self.audio_dir = os.path.join(get_package_share_directory('faulty_or_not'), 'audios')
        except Exception:
            self.audio_dir = os.path.join(os.path.dirname(__file__), '..', 'audios')

        self.get_logger().info('Mission node iniciado.')

    def figure_callback(self, msg):
        if self.mission_completed:
            return

        data = msg.data.strip()
        if ',' not in data:
            return

        parts = data.split(',')
        name = parts[0].strip()
        hex_color = parts[1].strip()

        if name not in self.figures:
            self.figures[name] = hex_color
            self.get_logger().info(f'Figura detectada: {name} ({hex_color}) [{len(self.figures)}/3]')

            if len(self.figures) == 3:
                self.process_mission()

    def process_mission(self):
        self.mission_completed = True
        self.get_logger().info('3 figuras detectadas. Iniciando ordenacao e acionamentos.')

        sorted_items = sorted(
            self.figures.items(),
            key=lambda x: int(x[1].replace('#', ''), 16),
            reverse=not self.order_ascending
        )

        sequence_str = ' -> '.join([item[0] for item in sorted_items])
        self.get_logger().info(f'Sequencia: {sequence_str}')

        seq_msg = String()
        seq_msg.data = sequence_str
        self.audio_seq_pub.publish(seq_msg)

        self.play_audios(sorted_items)
        self.trigger_relay()

        done_msg = Bool()
        done_msg.data = True
        self.done_pub.publish(done_msg)
        self.get_logger().info('Missao finalizada com sucesso. /mission/done publicado.')

    def play_audios(self, sorted_items):
        name_map = {
            'triangulo': 'triangulo.wav',
            'circulo': 'circulo.wav',
            'hexagono': 'hexagono.wav'
        }

        for name, _ in sorted_items:
            clean_name = name.lower().replace('â', 'a').replace('ã', 'a').replace('í', 'i')
            filename = name_map.get(clean_name, f'{clean_name}.wav')
            file_path = os.path.join(self.audio_dir, filename)

            if os.path.exists(file_path):
                self.get_logger().info(f'Tocando {filename}...')
                subprocess.run(['aplay', file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            else:
                self.get_logger().warn(f'Arquivo de audio nao encontrado: {file_path}')

    def trigger_relay(self):
        if not self.relay_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn('Servico MAVROS de comando indisponivel. Pulando acionamento do rele.')
            return

        req = CommandLong.Request()
        req.command = 181
        req.param1 = float(self.relay_id)
        req.param2 = 1.0

        future = self.relay_client.call_async(req)
        self.get_logger().info(f'Comando de rele {self.relay_id} enviado.')

def main(args=None):
    rclpy.init(args=args)
    node = MissionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
