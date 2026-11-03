import cv2
import numpy as np
import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge
from sensor_msgs.msg import Image
from std_msgs.msg import String

class VisionNode(Node) :
    def __init__(self):
        super().__init__('vision_node')
        #Declaracao de parametros
        self.declare_parameter('n_frames_vote', 5)
        self.n_frames_vote = self.get_parameter('n_frames_vote').value

        self.bridge = CvBridge()

        self.figure_pub = self.create_publisher(String, '/detected_figure', 10)
        self.debug_pub = self.create_publisher(Image, '/vision/debug_image', 10)
        self.image_sub = self.create_subscription(Image, '/camera/image_raw', self.image_callback, 10)

        #Variaveis de memoria
        self.current_detection_count = 0
        self.last_detected_figure = None
        self.published_figures = []

    def get_shape(self, contour):
        """Conta os vértices para descobrir a forma geométrica"""
        #Aproxima o contorno para um polígono
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, 0.04 * perimeter, True) #Simplifica o contorno para linhas retas, ignorando ruidos da imagem
        vertices = len(approx)

        if vertices == 3:
            return "Triangulo"
        elif vertices == 6:
            return "Hexagono"
        elif vertices > 6: #Um circulo aproximado tera muitos vertices
            return "Circulo"
        return None

    def image_callback(self, msg):
        cv_image = self.bridge.imgmsg_to_cv2(msg, "bgr8")
        hsv_image = cv2.cvtColor(cv_image, cv2.COLOR_BGR2HSV)
        debug_image = cv_image.copy() #Cria uma copia da imagem original para desenhar as anotacoes sem estragar a imagem real

        #Dicionario com as faixas de cor e os respetivos codigos HEX
        expected_colors = {
            "#FF0000": (np.array([0, 150, 100]), np.array([10, 255, 255])),     #Vermelho
            "#00FF00": (np.array([40, 100, 100]), np.array([80, 255, 255])),    #Verde
            "#0000FF": (np.array([100, 150, 100]), np.array([140, 255, 255]))   #Azul
        }

        for hex_code, (lower_color, upper_color) in expected_colors.items():
            mask = cv2.inRange(hsv_image, lower_color, upper_color)
            contours_color, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

            for contour in contours_color:
                if cv2.contourArea(contour) > 1000: #So analisa a forma se a mancha de cor for grande o suficiente
                    shape = self.get_shape(contour)
                    
                    if shape:
                        result = f"{shape}, {hex_code}"
                        
                        #Desenha na imagem de depuracao
                        x, y, w, h = cv2.boundingRect(contour)
                        cv2.rectangle(debug_image, (x, y), (x+w, y+h), (0, 255, 255), 2)
                        cv2.putText(debug_image, result, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)

                        #Filtro de frames
                        if result not in self.published_figures:
                            if result == self.last_detected_figure:
                                self.current_detection_count += 1
                            else:
                                self.last_detected_figure = result
                                self.current_detection_count = 1

                            #Publica se atingiu o numero de frames exigido
                            if self.current_detection_count >= self.n_frames_vote:
                                        msg_pub = String()
                                        msg_pub.data = result
                                        self.figure_pub.publish(msg_pub)
                                        self.published_figures.add(result)
                                        self.get_logger().info(f"Figura publicada: {result}")
                                        self.current_detection_count = 0 #Reseta o contador

        #Publica a imagem anotada para o relatorio
        self.debug_pub.publish(self.bridge.cv2_to_imgmsg(debug_image, "bgr8"))

def main(args=None):
    rclpy.init(args=args)
    node = VisionNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
