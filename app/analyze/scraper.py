import json
import os
from typing import Optional

import requests
from analyze.schemas import KSAttributes
from analyze.utils import read_file

DIR_NAME = "resources"
DIR_PATH = "./resources/_"
FILE_PATH = DIR_PATH + "{auction_id}_{file_name}"


class ParserWeb:

    def __init__(self, url: str) -> None:
        self.url: str = url
        self.attributes: Optional[KSAttributes] = None

    def is_real_url(self) -> bool:
        result = requests.get(self.url)
        return result.status_code == 200

    def get_attributes_ks(self) -> Optional[KSAttributes]:
        try:
            auction_id = self.url.split("/")[-1]
            result = json.loads(
                requests.get(
                    f"https://zakupki.mos.ru/newapi/api/Auction/Get?auctionId={auction_id}"
                ).content.decode()
            )
            result = KSAttributes(
                auction_id=auction_id,
                files=[
                    {
                        "name": file["name"],
                        "downloads_link": f"https://zakupki.mos.ru/newapi/api/FileStorage/Download?id={file['id']}",
                    }
                    for file in result["files"]
                ],
                files_parsed=[],
                name=result["name"],
                isContractGuaranteeRequired=(
                    result["contractGuaranteeAmount"]
                    if result["isContractGuaranteeRequired"]
                    else False
                ),
                isLicenseProduction=(
                    result["uploadLicenseDocumentsComment"]
                    if result["isLicenseProduction"]
                    else False
                ),
                deliveries=result["deliveries"],
                startCost=result["startCost"],
                contractCost=result["contractCost"],
            )
            return result
        except Exception as error:
            print(error)
            return None

    def fetch_and_parse(self) -> Optional[KSAttributes]:
        return self.get_attributes_ks() if self.is_real_url() else None


class FilesProcessor:

    def __init__(self):
        pass

    @staticmethod
    def download_file(download_link: str, file_name: str, auction_id: int) -> None:
        response = requests.get(download_link, stream=True)
        response.raise_for_status()

        os.makedirs(DIR_NAME, exist_ok=True)

        file_path = FILE_PATH.format(auction_id=auction_id, file_name=file_name)
        with open(file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    file.write(chunk)

    @staticmethod
    def parse_file_data(file_name: str, auction_id: int) -> str:
        file_path = FILE_PATH.format(auction_id=auction_id, file_name=file_name)
        file_text = read_file(file_path)
        return file_text

    def process_file(self, download_link, file_name, auction_id) -> str:
        self.download_file(download_link, file_name, auction_id)
        return self.parse_file_data(file_name, auction_id)

    def generate_parsed_files_data(self, page_data: KSAttributes):
        for file in page_data.files:
            page_data.files_parsed.append(
                self.process_file(
                    file["downloads_link"], file["name"], page_data.auction_id
                )
            )
        return page_data
