from py2neo import Graph

graph = Graph("http://localhost:7474", auth=("neo4j", "XzJEunfiT2G.t2Y"), name="neo4j")

def query_knowledge_graph(id):
    query = f"""
    MATCH (i:Identity {{name: '{id}'}})-[:HAS_JOB]->(j:Job)
    MATCH (i)-[:HAS_ADDRESS]->(a:Address)
    MATCH (i)-[:HAS_SALARY]->(s:Salary)
    MATCH (i)-[:CONTAINS]->(k:Keyword)
    RETURN j.title AS Job_Title, a.name AS Address, s.name AS Salary_Range, COLLECT(k.name) AS Keywords, i.repsonsibility AS Responsibility

    """

    result = graph.run(query).data()
    return result

if __name__ == "__main__":
    id = input("请输入ID：")
    result = query_knowledge_graph(id)

    for item in result:
            print(item)

