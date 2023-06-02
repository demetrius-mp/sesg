import trio  # type: ignore  # this file is only for example purposes
from sesg.evaluation import EvaluationFactory, Study
from sesg.scopus import InvalidStringError, Page, ScopusClient


API_KEYS: list[str] = []

GS: list[Study] = []
QGS: list[Study] = []


async def main():
    string = 'TITLE-ABS-KEY("machine learning" and "code smell") AND PUBYEAR > 2010 AND PUBYEAR < 2020'  # noqa: E501
    evaluation_factory = EvaluationFactory(gs=GS, qgs=QGS)

    client = ScopusClient(API_KEYS)

    entries: list[Page.Entry] = []
    try:
        async for page in client.search(string):
            entries.extend(page.entries)

    except InvalidStringError:
        print("Invalid string")

    evaluation = evaluation_factory.evaluate([e.title for e in entries])

    print(evaluation.start_set_recall)
    # 0.7


if __name__ == "__main__":
    trio.run(main)
