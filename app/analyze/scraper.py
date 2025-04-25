import json
from typing import Optional

import requests
from analyze.schemas import KSAttributes


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
