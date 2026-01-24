class Reel:

    def __init__(self, id, products, shortDescription, longDescription, url, hashtags, influencer=None):
        self.id = id
        self.products = products
        self.shortDescription = shortDescription
        self.longDescription = longDescription
        self.url = url
        self.hashtags = hashtags
        self.influencer = influencer or {}