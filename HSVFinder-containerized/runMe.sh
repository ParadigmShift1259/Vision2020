sudo docker run -it --net=host --env="DISPLAY" --volume="$HOME/.Xauthority:/root/.Xauthority:rw" --device=/dev/video0 agastya12/hsv-finder:latest
