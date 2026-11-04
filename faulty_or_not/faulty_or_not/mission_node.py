#!/usr/bin/env python3
import os
import shutil
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

        self.audio_dir = None
        try:
            share_dir = os.path.join(get_package_share_directory('faulty_or_not'), 'audios')
            if os.path.exists(share_dir):
                self.audio_dir = share_dir
        except Exception:
            pass

        if not self.audio_dir:
            local_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'audios'))
            if os.path.exists(local_dir):
                self.audio_dir = local_dir
            else:
                self.audio_dir = 'audios'

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

    def color_sort_key(self, hex_code):
        hex_clean = hex_code.replace('#', '').strip()
        return int(hex_clean, 16)

    def process_mission(self):
        self.mission_completed = True
        self.get_logger().info('3 figuras detectadas. Iniciando ordenacao e acionamentos.')

        sorted_items = sorted(
            self.figures.items(),
            key=lambda x: self.color_sort_key(x[1]),
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
        import wave
        import time
        name_map = {
            'triangulo': 'triangulo.wav',
            'circulo': 'circulo.wav',
            'hexagono': 'hexagono.wav'
        }

        for name, _ in sorted_items:
            clean_name = name.lower().replace('â', 'a').replace('ã', 'a').replace('í', 'i').replace('á', 'a')
            filename = name_map.get(clean_name, f'{clean_name}.wav')
            file_path = os.path.join(self.audio_dir, filename)

            if os.path.exists(file_path):
                self.get_logger().info(f'Tocando {filename}...')
                duration = 2.0
                try:
                    with wave.open(file_path, 'rb') as w:
                        duration = w.getnframes() / float(w.getframerate())
                except Exception:
                    pass

                if shutil.which('paplay'):
                    subprocess.run(['paplay', file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                elif shutil.which('aplay'):
                    subprocess.run(['aplay', file_path], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                else:
                    subprocess.run(f"ffmpeg -loglevel quiet -i '{file_path}' -f wav - | paplay", shell=True)

                # Aguarda o audio terminar de tocar para nao sobrepor com o proximo
                time.sleep(duration + 0.3)
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
        if rclpy.ok():
            rclpy.shutdown()

if __name__ == '__main__':
    main()
