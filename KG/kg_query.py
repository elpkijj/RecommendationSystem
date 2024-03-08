from py2neo import Graph

graph = Graph("http://localhost:7474", auth=("neo4j", "XzJEunfiT2G.t2Y"), name="neo4j")

def query_knowledge_graph(identifier):
    query = f"""
    MATCH (i:Identity {{name: '{identifier}'}})
    MATCH (i)-[:HAS_JOB]->(j:Job)
    MATCH (i)-[:HAS_ADDRESS]->(a:Address)
    MATCH (i)-[:HAS_SALARY]->(s:Salary)
    MATCH (i)-[:CONTAINS]->(k:Keyword)
    OPTIONAL MATCH (i)-[:LOCATED_IN]->(c:City)
    RETURN j.title AS Job_Title, a.name AS Address, s.name AS Salary_Range, COLLECT(k.name) AS Keywords, i.repsonsibility AS Responsibility, c.name AS City
    """

    result = graph.run(query).data()
    return result

if __name__ == "__main__":
    identifier = input("请输入ID：")
    result = query_knowledge_graph(identifier)

    if result:
        for item in result:
            print(item)
    else:
        print(f"No information found for the Identity/Keyword: {identifier}")
