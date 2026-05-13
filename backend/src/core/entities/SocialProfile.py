

class SocialProfile:
    def __init__(self, json_data: dict):
        self.name = json_data["name"]
        self.platform = json_data["platform"]
        self.link = json_data["link"]
        self.bio = json_data["bio"]
        self.picture_link = str(json_data["picture_link"])
        self.additional_images = [str(image["image_link"]) for image in json_data["additional_images"]]

    def get_all_images_links(self) -> list[str]:
        images_links = [self.picture_link]
        for image in self.additional_images:
            images_links.append(image["image_link"])
        return images_links



'''"profiles": [
{
"name": "Ori Steinberg",
"platform": "Facebook",
"link": "https://www.facebook.com/ori.steinberg.3",
"bio": "NO NIO",
"picture_link":
"https://scontent-atl3-1.xx.fbcdn.net/v/t1.6435-1/76751538_10157746676797491_105469074923
4282496_n.jpg?stp=cp0_dst-jpg_s80x80_tt6&_nc_cat=101&ccb=1-7&_nc_sid=1d2534&_nc_ohc
=ZdpRUlRpNboQ7kNvwENwdQT&_nc_oc=AdkM1_9EjI0pvYr_3NroiR3jmIKusO97nnQILWwqAh
DM0VywyEUKyelo0jEQQkFWy-D7fdEk9tqHgsh9eR-8Fl6F&_nc_zt=24&_nc_ht=scontent-atl3-1.x
x&_nc_gid=yMnObEBIBb6Ws2SE7NYAnQ&oh=00_AfunEuyrP4EEvkXoj4xCtNX3zjDwAxu4rf3K5
1lEjG4OQA&oe=69B32D8B",
"additional_images": [
{
"image_link":
"https://scontent-atl3-1.xx.fbcdn.net/v/t1.6435-1/76751538_10157746676797491_105469074923
4282496_n.jpg?stp=cp0_dst-jpg_s80x80_tt6&_nc_cat=101&ccb=1-7&_nc_sid=1d2534&_nc_ohc
=ZdpRUlRpNboQ7kNvwENwdQT&_nc_oc=AdkM1_9EjI0pvYr_3NroiR3jmIKusO97nnQILWwqAh
DM0VywyEUKyelo0jEQQkFWy-D7fdEk9tqHgsh9eR-8Fl6F&_nc_zt=24&_nc_ht=scontent-atl3-1.x
x&_nc_gid=yMnObEBIBb6Ws2SE7NYAnQ&oh=00_AfunEuyrP4EEvkXoj4xCtNX3zjDwAxu4rf3K5
1lEjG4OQA&oe=69B32D8B"
}'''