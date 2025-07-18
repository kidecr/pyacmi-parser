from acmikit.parser import ACMILoader

for idx, frame in enumerate(ACMILoader.from_file('./data/flyingdata0.acmi')):
    print(f'--- Frame {idx} @ {frame.timestamp:.2f}s ---')
    for obj in frame.objects:
        print(f'  {obj.object_id:06X}  {obj.object_coordinates}  {obj.object_properties}')