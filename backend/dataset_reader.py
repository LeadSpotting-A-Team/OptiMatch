import csv
import metadata as metadata_module

def read_dataset_as_csv(path : str):

    posts_metadata = []#list of posts metadata

    with open(path, 'r', encoding='utf-8') as file:
        #read the dataset as a csv file with utf-8 encoding (read mode)
        reader = csv.reader(file)
        row_index = 0
        columns_names = {}
        for row in reader:
            if(row_index == 0): #first row - read column names
                column_index = 0
                for column_name in row:
                    columns_names[column_name] = column_index
                    column_index += 1
                row_index += 1
                continue #skip header row
            row_index += 1
            post_matadata = metadata_module.Post_Metadata(row[columns_names["post_id"]],
            row[columns_names["mediaurl"]], 
            row[columns_names["link"]], 
            row[columns_names["creation_time"]], 
            row[columns_names["source"]])
            posts_metadata.append(post_matadata)

    return posts_metadata#[post_matadata1 , post_matadata2 , post_matadata3 , ...]