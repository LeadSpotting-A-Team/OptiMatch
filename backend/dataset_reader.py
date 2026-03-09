import csv
import metadata as metadata_module


#define function to read the dataset as a csv file and return the list of posts metadata
#path: the path to the csv file
#return: the list of posts metadata
def read_dataset_as_csv(path : str , post_id_column_name : str = "post_id", media_url_column_name : str = "mediaurl", link_column_name : str = "link", timestamp_column_name : str = "creation_time", platform_column_name : str = "source"):

    posts_metadata = []#list of posts metadata

    with open(path, 'r', encoding='utf-8-sig') as file:
        #read the dataset as a csv file with utf-8 encoding (read mode)
        reader = csv.reader(file)
        row_index = 0
        columns_names = {}
        for row in reader:
            if(row_index == 0): #first row - read column names
                column_index = 0
                for column_name in row:
                    columns_names[column_name] = column_index
                    #print(f"Column name: {column_name} - Column index: {column_index}")
                    column_index += 1
                row_index += 1
                continue #skip header row
            row_index += 1
            post_metadata = metadata_module.Post_Metadata(
            row[columns_names[post_id_column_name]],
            row[columns_names[media_url_column_name]], 
            row[columns_names[link_column_name]], 
            row[columns_names[timestamp_column_name]], 
            row[columns_names[platform_column_name]])
            posts_metadata.append(post_metadata)

    return posts_metadata#[post_matadata1 , post_matadata2 , post_matadata3 , ...]