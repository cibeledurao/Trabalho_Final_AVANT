#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from mavros_msgs.srv import CommandBool, SetMode, CommandTOL, ParamSetV2
from geometry_msgs.msg import PoseStamped
from std_msgs.msg import Bool
from rclpy.qos import qos_profile_sensor_data
from rclpy.signals import SignalHandlerOptions
from rcl_interfaces.msg import ParameterValue, ParameterType
import time
import math

MAX_SPEED = 0.8

class CoverageMission(Node):
    def __init__(self):
        super().__init__('coverage_mission_5')
        self.get_logger().info('Esperando conexão com MAVROS...')


        self.x = self.y = self.z = 0.0
        self.mission_done = False

        # Clientes para os serviços MAVROS
        self.set_mode_client = self.create_client(SetMode, '/mavros/set_mode')
        self.arming_client = self.create_client(CommandBool, '/mavros/cmd/arming')
        self.takeoff_client = self.create_client(CommandTOL, '/mavros/cmd/takeoff')
        self.land_client = self.create_client(CommandTOL, '/mavros/cmd/land')
        self.create_subscription(PoseStamped, '/mavros/local_position/pose', self.pose_cb, qos_profile_sensor_data)
        self.param_client = self.create_client(ParamSetV2, '/mavros/param/set')

        #Executa o tópico do mission_node
        self.create_subscription(Bool, '/mission/done', self.mission_done_cb, 10)

        #Publisher da posição 
        self.local_position = self.create_publisher(PoseStamped, '/mavros/setpoint_position/local', 10)

        # Aguarda convexão MAVROS
        # Qualquer service pode ser usado para testar a conexão, não necessariamente o arming
        while rclpy.ok() and not self.arming_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn('Aguardando serviços do MAVROS...')

        # Roda o movimento
        self.get_logger().info('Conexão estabelecida. Iniciando missão.')
        self.run_mission()
    def mission_done_cb(self,msg):
        if msg.data:
            self.mission_done = True

    def set_speed(self, speed_mps):
        req = ParamSetV2.Request()
        req.param_id = 'WPNAV_SPEED'
        req.value = ParameterValue()
        req.value.type = ParameterType.PARAMETER_DOUBLE
        req.value.double_value = float(speed_mps * 100)

        future = self.param_client.call_async(req)
        start_time = time.time()
        while rclpy.ok() and not future.done() and (time.time() - start_time < 3.0):
            rclpy.spin_once(self, timeout_sec=0.1)

        if future.result() is not None and future.result().success:
            self.get_logger().info(f'Velocidade máxima definida para {speed_mps} m/s.')
        else:
            self.get_logger().warn('Falha ao definir a velocidade máxima.')

    def set_mode(self, mode_name):
        req = SetMode.Request()
        req.custom_mode = mode_name

        future = self.set_mode_client.call_async(req)
        start_time = time.time()
        while rclpy.ok() and not future.done() and (time.time() - start_time < 3.0):
            rclpy.spin_once(self, timeout_sec=0.1)

        if future.result() is not None and future.result().mode_sent:
            self.get_logger().info(f'Modo {mode_name} definido.')
            return True
        self.get_logger().warn(f'Falha ao definir o modo {mode_name}')
        return False

    def arm(self):
        req = CommandBool.Request()
        req.value = True
        future = self.arming_client.call_async(req)
                    
        start_time = time.time()
        while rclpy.ok() and not future.done() and (time.time() - start_time < 3.0):
            rclpy.spin_once(self, timeout_sec=0.1)

        if future.result() is not None and future.result().success:
            self.get_logger().info('Drone armado.')
            return True
        self.get_logger().warn('Falha ao armar o drone.')
        return False

    def takeoff(self, altitude=5.0):
        req = CommandTOL.Request()
        req.altitude = float(altitude)
        self.get_logger().info(f'Enviando solicitação de decolagem para {altitude} m...')

        future = self.takeoff_client.call_async(req)

        start_time = time.time()
        while rclpy.ok() and not future.done() and (time.time() - start_time < 4.0):
            rclpy.spin_once(self, timeout_sec=0.1)

        res = future.result()
        if res is not None and res.success:
            self.get_logger().info(f'Decolagem aceita: subindo para {altitude} m.')
            return True

        self.get_logger().warn(f'Falha ou timeout ao solicitar a decolagem. Resposta: {res}')
        return False

    def pose_cb(self, msg):
        self.x = msg.pose.position.x
        self.y = msg.pose.position.y
        self.z = msg.pose.position.z

    def send_position(self, x,y,z, duration_sec=5.0):
            pose = PoseStamped()
            pose.header.frame_id = 'map'
            pose.pose.orientation.w = 1.0
            pose.pose.position.x = float(x)
            pose.pose.position.y = float(y)
            pose.pose.position.z = float(z)

            start = time.time()
            while rclpy.ok() and time.time() - start < duration_sec:
                if self.mission_done:
                    break
                pose.header.stamp = self.get_clock().now().to_msg()
                self.local_position.publish(pose)
                rclpy.spin_once(self, timeout_sec=0.05)
            return False
    
    def land(self):
        self.get_logger().warn('Comando pouso.')
        req = CommandTOL.Request()
        future = self.land_client.call_async(req)

        start_time = time.time()
        while rclpy.ok() and not future.done() and (time.time() - start_time < 3.0):
            rclpy.spin_once(self, timeout_sec=0.1)

        if future.result() is not None and future.result().success:
            self.get_logger().info('Pousando...')
        else:
            self.get_logger().warn('Falha ao acionar o pouso.')

    def emergency_land(self):
        self.get_logger().info("Interrupção detectada. Iniciando pouso de emergência...")
        dist = math.hypot(self.x, self.y)
        self.send_position(0.0, 0.0, self.z, duration_sec=dist / MAX_SPEED + 1.0)
        self.land()

    def run_mission(self):
        try:
            time.sleep(1.0)  
            
            if not self.set_mode("GUIDED"):
                self.get_logger().error('Não foi possível entrar em GUIDED. Abortando.')
                return

            time.sleep(0.5)

            if not self.arm():
                return

            time.sleep(0.5)

            if not self.takeoff(6.5):
                return

            self.set_speed(MAX_SPEED) 

            self.get_logger().info('Subindo para a altura de varredura (6.5m).')
            start = time.time()
            while rclpy.ok() and self.z < 5.85 and time.time() - start < 15.0:
                rclpy.spin_once(self, timeout_sec=0.1)
            self.get_logger().info(f'Altitude atingida: z={self.z:.2f}')

            points = [
                (-7.0,  3.0, 6.5),  
                (-7.0, -3.0, 6.5),  
                (-4.2, -3.0, 6.5),
                (-4.2,  3.0, 6.5),
                (-1.4,  3.0, 6.5),
                (-1.4, -3.0, 6.5),
                ( 1.4, -3.0, 6.5),
                ( 1.4,  3.0, 6.5),
                ( 4.2,  3.0, 6.5),
                ( 4.2, -3.0, 6.5),
                ( 7.0, -3.0, 6.5),  
                ( 7.0,  3.0, 6.5)   
            ]

            for i, p in enumerate(points):
                if self.mission_done:
                    self.get_logger().info('Todas as figuras detectadas. Interrompendo varredura...')
                    break

                self.get_logger().info(f'Coordenada {i+1}: {p}')
                dist = ((p[0]-self.x)**2 + (p[1]-self.y)**2) ** 0.5
                self.send_position(p[0], p[1], p[2], duration_sec=dist/MAX_SPEED + 5.5) #diminuir se der

            self.get_logger().info('A retornar à origem (0, 0)...')
            dist_home = math.hypot(self.x, self.y)
            self.send_position(0.0, 0.0, 6.5, duration_sec=(dist_home/MAX_SPEED) + 5.0)

            self.get_logger().info('Varredura concluída. Pousando...')
            self.land()

        except KeyboardInterrupt:
            self.emergency_land()

def main(args=None):
    rclpy.init(args=args, signal_handler_options=SignalHandlerOptions.NO)
    node = CoverageMission()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
