As a programmer

# insturction: write an program that transfer the rtsp received to the annotated rtsp

# context: 
    1. you might use django framework and the model to save the currentFrame 
    2. you might use FIFO to save the tmp video for the annotated rtsp 
    3. you might write an ai inference service 
    4. you might async the ai inference result to the video that receive, because there might be time difference between before and after ai inference 
    5. since the frequency of the annotated result from ai inference is difference with the input, try to extend the annotated result in the video, need to let the video looks smooth 
    6. you might calculate the position of the bbox of the difference annotated result within timestamp and automatic generate then rtsp output generator in order to not missing each frame of the input

Think step-by-step, if you have any suggestions and questions feel free to ask me