import argparse
import json
import sys
import numpy as np
import cv2 as cv
from common import VisionInstance
from HighGoal import HighGoal
import imagezmq

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='2036 vision process.')
    parser.add_argument('config', metavar='config', type=str, help='file to parse for config')
    parser.add_argument('--debug',action='store_true', help='run debug functions for layers in addition to standard run')
    parser.add_argument('--remote', help="uses imagezmq to stream debug outputs over the network")
    parser.set_defaults(debug=False)

    args = parser.parse_args()
    
    fileName = args.config

    data = ""
    with open(fileName, 'r') as file:
        data = file.read().replace('\n', '')

    instance = VisionInstance(data)
    sender = None
    if args.remote:
        sender = imagezmq.ImageSender(connect_to=f'tcp://{args.remote}:5800', REQ_REP=False)

    # MARK: Where to define layers
    layers = [
        HighGoal(instance)
    ]

    if sys.platform.startswith('linux'):
        instance.log("Detected Linux system. Adding layers that only work with Linux (tflite_runtime dependent)...")
        from BallVision import BallVision
        layers.append(BallVision(instance))
        
    while True:
        for layer in layers:
            layer.run()
            if args.debug:
                layer.debug()
            if args.remote:
                output = layer.stream()
                sender.send_image(output[0], output[1])

        if cv.waitKey(1) == ord('q'):
            break

    instance.cleanup()
    cv.destroyAllWindows()