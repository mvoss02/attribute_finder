from data_preprocessing import data_loading, post_data

def main():
    # Load data from the API and merge with attributes
    data_loading.process_data()

    # Post data to the database
    post_data.post_articles_to_db()


if __name__ == '__main__':
    main()
