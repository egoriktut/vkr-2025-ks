from analyze.scraper import FilesProcessor, ParserWeb


def process_data(urls):
    ks_validators_dict = {}
    for url in urls:
        page_data = ParserWeb(url).fetch_and_parse()
        page_data = FilesProcessor().generate_parsed_files_data(page_data)
        ks_validators_dict[url] = page_data
    return ks_validators_dict


def write_db(task_result):
    print(task_result.result)
