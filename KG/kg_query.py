from py2neo import Graph

graph = Graph("http://localhost:7474", auth=("neo4j", "XzJEunfiT2G.t2Y"), name="neo4j")

def query_knowledge_graph(job_title):
    query = f"""
    MATCH (j:Job {{title: '{job_title}'}})-[:RECRUIT_BY]->(id:Identity),
          (id)-[:HAS_CONTACT]->(contact:Contact),
          (id)-[:HAS_COMPANY]->(company:Company),
          (id)-[:HAS_ADDRESS]->(address:Address),
          (id)-[:HAS_WEBSITE]->(website:Website),
          (id)-[:REQUIRES]->(edu:EducationRequirement),
          (id)-[:CONTAINS]->(keyword:Keyword)
    RETURN id.name AS ID, contact.name AS Contact, company.name AS Company, 
           address.name AS Address, website.name AS Website, edu.name AS EducationRequirement, 
           COLLECT(keyword.name) AS Keywords
    """

    result = graph.run(query).data()
    return result

if __name__ == "__main__":
    job_title = input("请输入期望岗位：")
    result = query_knowledge_graph(job_title)

    if result:
        for item in result:
            print(item)
    else:
        print("未找到相关信息")