import os
import IVF

index_path = input("Enter the path to the index file: ")
if not os.path.exists(index_path):
    print(f"Index file {index_path} does not exist")
    exit()

map_path = os.path.splitext(index_path)[0] + ".map.json"
ivf = IVF.FaceVectorStore(index_path, map_path)

new_nlist = int(input("Enter the new nlist: "))

training_data = ivf.get_all_embeddings()
if len(training_data) < new_nlist * 39:
    print(f"Not enough vectors: need {new_nlist * 39}, have {len(training_data)}")
    exit()

ivf.rebuild_and_train(training_data, new_nlist)
print(f"Rebuilt successfully with nlist={new_nlist}")