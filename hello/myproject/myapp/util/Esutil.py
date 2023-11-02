from elasticsearch import Elasticsearch

class EsUtil:

    def __init__(self, username, password, url):
        self.username = username
        self.password = password
        self.url = url

    def get_client_factory(self):
        es = Elasticsearch(
            [self.url],
            http_auth=(self.username, self.password),
            scheme="https",  # Use "http" if your Elasticsearch instance is not secured with SSL/TLS
            port=443,        # Change the port number if your Elasticsearch instance is using a different port
        )
        return es

# Example usage
if __name__ == "__main__":
    # Replace these values with your Elasticsearch credentials and URL
    es_username = "your_username"
    es_password = "your_password"
    es_url = "https://your_elasticsearch_url"

    es_util = EsUtil(es_username, es_password, es_url)
    es_client = es_util.get_client_factory()
