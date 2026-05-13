import requests


class SocialProfile:
    def __init__(self, name: str, platform: str, link: str, bio: str, picture_link: str, additional_images: list[str]):
        self.name = name
        self.platform = platform
        self.link = link
        self.bio = bio
        self.picture_link = picture_link
        self.additional_images = additional_images

    def get_all_images_links(self) -> list[str]:
        images_links = [self.picture_link]
        for image in self.additional_images:
            img_link = image.get("image_link")
            if img_link is not None:
                images_links.append(img_link)
        return images_links



def get_profiles_count_from_api(first_name: str, last_name: str) -> int:

    #we gets the number of results from the api on that spacific fullname
    url = f"https://api.leadspotting.com/Customers.jsp?Command=DiscoverNewProfile&Name={first_name}%20{last_name}"
    response = requests.get(url)
    if response.status_code != 200:
        return len(get_profiles_from_api(first_name, last_name))
    return response.json()["numberOfResults"]


def get_profiles_from_api(first_name: str, last_name: str) -> list[SocialProfile]:
    #we gets the number of results from the api on that spacific fullname
    url = f"https://api.leadspotting.com/Customers.jsp?Command=SocialProfileSearch&Name={first_name}%20{last_name}"
    response = requests.get(url)
    if response.status_code != 200:
        return []
    profiles = []
    for profile in response.json()["profiles"]:
        name = profile.get("name","invalid_name")
        platform = profile.get("platform","unknown platform")
        link = profile.get("link","invalid_link")
        bio = profile.get("bio","invalid_bio")
        picture_link = profile.get("picture_link","invalid_picture_link")
        additional_images = profile.get("additional_images",[])

        profiles.append(SocialProfile(name, platform, link, bio, picture_link, additional_images))
    return profiles
