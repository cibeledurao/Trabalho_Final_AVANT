#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from mavros_msgs.srv import CommandBool, SetMode, CommandTOL
import time

class SimpleTakeoffLand(Node):
    def __init__(self):
        super().__init__('simple_takeoff_land')
        self.get_logger().info('Esperando conexão com MAVROS...')

        # Clientes para os serviços MAVROS
        self.set_mode_client = self.create_client(SetMode, '/mavros/set_mode')
        self.arming_client = self.create_client(CommandBool, '/mavros/cmd/arming')
        self.takeoff_client = self.create_client(CommandTOL, '/mavros/cmd/takeoff')
        self.land_client = self.create_client(CommandTOL, '/mavros/cmd/land')

        # Aguarda convexão MAVROS
        # Qualquer service pode ser usado para testar a conexão, não necessariamente o arming
        while rclpy.ok() and not self.arming_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().warn('Aguardando serviços do MAVROS...')

        # Roda o movimento
        self.get_logger().info('Conexão estabelecida. Iniciando sequência de voo.')
        self.run_mission()

    def set_mode(self, mode_name):
            req = SetMode.Request()
            req.custom_mode = mode_name

            future = self.set_mode_client.call_async(req)
            
            rclpy.spin_until_future_complete(self, future)
            if future.result() is not None and future.result().mode_sent:
                self.get_logger().info(f'Modo {mode_name} definido.')

    def arm(self):
        req = CommandBool.Request()
        req.value = True
        self.arming_client.call_async(req)

        future = self.arming_client.call_async(req)
                    
        rclpy.spin_until_future_complete(self, future)
        if future.result().success:
            self.get_logger().info('Drone armado.')

    def takeoff(self, altitude=2.0):
        req = CommandTOL.Request()
        req.altitude = altitude
        self.takeoff_client.call_async(req)

        future = self.takeoff_client.call_async(req)
                            
        rclpy.spin_until_future_complete(self, future)
        if future.result().success:
            self.get_logger().info(f'Decolando para {altitude} metros.')

    def land(self):
        req = CommandTOL.Request()
        self.land_client.call_async(req)

        future = self.land_client.call_async(req)

        rclpy.spin_until_future_complete(self, future)
        if future.result().success:
            self.get_logger().info('Pousando...')

    def run_mission(self):
        self.set_mode("GUIDED")  # modo que permite controle por comandos
        time.sleep(1)
        self.arm()
        time.sleep(1)
        self.takeoff(altitude=2.0)
        time.sleep(8)        
        self.land()
        time.sleep(8)
        self.get_logger().info('Missão finalizada.')

def main(args=None):
    rclpy.init(args=args)
    node = SimpleTakeoffLand()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()