# Trabalho Final -faulty_or_not

Pacote ROS 2 do trabalho final trainee AVANT.

## Build

Dentro do workspace ROS 2 (onde fica a pasta `src`):

```bash
colcon build --packages-select faulty_or_not
source install/setup.bash
```

## Execução
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
