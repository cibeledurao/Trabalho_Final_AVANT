# Trabalho Final - Grupo 7 - faulty_or_not

Repositório do Desafio Final do trainee. Esse desafio teve como objetivo o desenvolvimento de uma navegação autônoma para um drone em ambiente simulado no Gazebo, processamento de visão computacional em espaço HSV para detecção de formas geométricas coloridas ordenadas por meio do seu código hexadecimal, reprodução de áudio e acionamento de relé via MAVlink.

## Dependências do sistema
Para executar esse projeto, é necessário que o ambiente possua as seguintes ferramentas e pacotes instalados:
* Ubuntu 22.04 LTS
* ROS 2
* Gazebo Simulator (com o modelo da arena e do drone configurados, isso está disponível na página do Notion da equipe)
* MAVROS / MAVLink

Os Pacotes ROS 2 utilizados foram (*package.xml*)
* rclpy
* sensor_msgs
* geometry_msgs
* std_msgs
* mavros_msgs
* cv_bridge
* ament_index_python

As bibliotecas externas utilizadas foram:
* cv2
* numpy
* wave (nativo do Python)
## Instalação e Configuração do Workspace
Dentro do workspace ROS 2 (onde fica a pasta `src`):
``` bash
Felipe me ajuda aqui!! Não dei git clone no meu pq n sei como q faz
Coloca oq tem q fazer aqui pfvvv
```
## Compilação
Dentro do seu workspace:
```bash
colcon build --packages-select faulty_or_not
source install/setup.bash
```

## Execução geral
Para rodar todos os nós ao mesmo tempo (navigation, vision e mission):
```bash
ros2 launch faulty_or_not mission.launch.py
```
Para rodar a imagem da câmera:
```bash
ros2 run rqt_image_view rqt_image_view
```
## Execução do navigation_node
``` bash
ros2 run faulty_or_not navigation_node
```
## Execução do vison_node
``` bash
ros2 run faulty_or_not vision_node
```
## Execução do mision_node
``` bash
ros2 run faulty_or_not mission_node
````
## Teste manual do mission_node
Com o no de missao rodando, envie os topicos pelo terminal:

```bash
ros2 topic pub /detected_figure std_msgs/msg/String "{data: 'Triangulo,#FF0000'}" --once
ros2 topic pub /detected_figure std_msgs/msg/String "{data: 'Hexagono,#00FF00'}" --once
ros2 topic pub /detected_figure std_msgs/msg/String "{data: 'Circulo,#0000FF'}" --once
```

Para verificar o resultado:
```bash
ros2 topic echo /audio_sequence
ros2 topic echo /mission/done
```
