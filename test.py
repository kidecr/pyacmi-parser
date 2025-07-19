from acmiparse.parser import load_acmi

file = load_acmi('./data/flyingdata0.acmi')

print(file.ids)
print(file.frames[0].objects[0].object_events)
print(file.columns[0])
print(file.id_objects(1))
print(file.id_to_csv([1]))

