# faulty_or_not

Pacote ROS 2 do trabalho final trainee AVANT.

## Build

Dentro do workspace ROS 2 (onde fica a pasta `src`):

```bash
colcon build --packages-select faulty_or_not
source install/setup.bash
```

## Execucao

Para rodar apenas o no de missao (Pessoa 3):
```bash
ros2 run faulty_or_not mission_node
```

Para rodar os tres nos juntos pelo launch:
```bash
ros2 launch faulty_or_not mission.launch.py
```

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
