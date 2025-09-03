import h5py

with h5py.File("./models/keras_model.h5", "r") as f:
    print(list(f.keys()))
