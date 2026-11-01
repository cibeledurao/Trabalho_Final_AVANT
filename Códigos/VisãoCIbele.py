#!/usr/bin/env python3

"""Ponto de partida para o nó do trainee.

Este nó já inicia com sucesso pelo launch mesmo sem solução implementada,
garantindo que o simulador rode sem erros. Preencha a solução abaixo:

Desafio:
  1. Assine /camera/image_raw (sensor_msgs/Image) e /camera/camera_info
     (sensor_msgs/CameraInfo).
  2. Localize a base circular verde com o marcador ArUco ID 0.
  3. Publique em /cmd_vel (geometry_msgs/Twist) as correções de posição
     para centralizar o drone sobre o alvo.
"""

import rclpy
from rclpy.node import Node

import math
import cv2
import numpy as np

from geometry_msgs.msg import Twist
from sensor_msgs.msg import CameraInfo, Image
from cv_bridge import CvBridge


class TraineeVisionNode(Node):
    """Estrutura inicial: preencha com a sua solução de visão computacional."""

    def __init__(self):
        super().__init__('trainee_vision_node')
        self._dictionary = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_50) #achei essa linha no node de simulação
        self._parameters = cv2.aruco.DetectorParameters()
        self._detector = cv2.aruco.ArucoDetector(self._dictionary, self._parameters)

        self._bridge = CvBridge()
        self.z = 5.0
        self.concluido = False

        # Registre aqui as assinaturas e publicadores da sua solução.
        self.create_subscription(CameraInfo, '/camera/camera_info', self.camera_info_callback, 10)
        self.create_subscription(Image, '/camera/image_raw', self._image_callback, 10)
        self.cmd_pub = self.create_publisher(Twist, '/cmd_vel', 10)

        self.get_logger().info(
            'Nó do trainee rodando. Implemente a sua solução neste arquivo!')

    def _image_callback(self, message):
        """Chamado a cada nova imagem da câmera do simulador."""
        #self.get_logger().info('Imagem recebida')
        if self.concluido:
            return

        msg_imagem = self._bridge.imgmsg_to_cv2(message, "bgr8")

        gray_scale = cv2.cvtColor(msg_imagem, cv2.COLOR_BGR2GRAY)
        corners, ids, rejected = self._detector.detectMarkers(gray_scale)

        twist = Twist()

        if ids is not None:
            #cv2.aruco.drawDetectedMarkers(msg_imagem, corners, ids) tava piorando
            flat_ids = ids.flatten()

            if 0 in flat_ids:
                self.get_logger().info("Círculo verde encontrado!")
             
                index = np.where(flat_ids == 0)[0][0]
                marker_corners = corners[index][0]
                
                x_min = int(np.min(marker_corners[:, 0]))
                x_max = int(np.max(marker_corners[:, 0]))
                y_min = int(np.min(marker_corners[:, 1]))
                y_max = int(np.max(marker_corners[:, 1]))
                
                padding = int(max(x_max-x_min, y_max-y_min))
                h, w, _ = msg_imagem.shape
                x_min = max(0, x_min - padding)
                x_max = min(w, x_max + padding)
                y_min = max(0, y_min - padding)
                y_max = min(h, y_max + padding)
                
                recorte = msg_imagem[y_min:y_max, x_min:x_max]
                
                if recorte.size > 0:
                    hsv = cv2.cvtColor(recorte, cv2.COLOR_BGR2HSV)
                    menor_green = np.array([35, 40, 40]) #usei como base os valores do nó de
                    maior_green = np.array([90, 255, 255])
                    mask = cv2.inRange(hsv, menor_green, maior_green)
                    
                    green_pixels = cv2.countNonZero(mask)
                    total_pixels = mask.shape[0] * mask.shape[1]
                    green_pct = (green_pixels / total_pixels) * 100 if total_pixels > 0 else 0
                    
                    if green_pct > 10:
                        centro_x = float(np.mean(marker_corners[:, 0]))
                        centro_y = float(np.mean(marker_corners[:, 1]))
                        
                        center_x_img = w / 2.0
                        center_y_img = h / 2.0

                        error_x = centro_x - center_x_img
                        error_y = centro_y - center_y_img

                        tolerancia = 5 #achei com testes, se for muito pequeno ou muito grande o drone nunca pousa, começa a sambar

                        ajuste = 0.008 #não estava centralizado, aumentei para que perto do centro a correção fique maior
                        twist.linear.x = ajuste*error_x
                        twist.linear.y = ajuste*error_y


                        if abs(error_x) < tolerancia and abs(error_y) < tolerancia:
                            twist.linear.z = -4.0
                            self.get_logger().info("Pousando")
                            self.z += twist.linear.z*0.05 #camera tem 20 Hz
                            if self.z <= 0.2: #valor decidido por testes
                                self.concluido = True
                                twist = Twist()
                                self.get_logger().info("Missão concluida com sucesso!")
                                

                        self.cmd_pub.publish(twist)

                    else:
                        self.get_logger().info("Circulo verde não encontrado")
            else:
                self.get_logger().info("Circulo verde não encontrado")

        
        cv2.waitKey(1)


    def camera_info_callback(self, msg):
        self.camera_matrix = np.array(msg.k, dtype=np.float32).reshape(3, 3)
    
        self.dist_coeffs = np.array(msg.d, dtype=np.float32)

def main(args=None):
    rclpy.init(args=args)
    node = TraineeVisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()
        cv2.destroyAllWindows()


if __name__ == '__main__':
    main()
