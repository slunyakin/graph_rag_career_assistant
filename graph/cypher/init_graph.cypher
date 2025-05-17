// Clear existing data
MATCH (n) DETACH DELETE n;

// Create constraints
CREATE CONSTRAINT IF NOT EXISTS FOR (r:Role) REQUIRE r.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (l:Level) REQUIRE l.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (resp:Responsibility) REQUIRE resp.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (cp:CorePrinciple) REQUIRE cp.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (s:Skill) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (sc:ScopeOfCommunication) REQUIRE sc.name IS UNIQUE;
CREATE CONSTRAINT IF NOT EXISTS FOR (i:Impact) REQUIRE i.name IS UNIQUE;

// Create indexes for better query performance
CREATE INDEX IF NOT EXISTS FOR (r:Role) ON (r.name);
CREATE INDEX IF NOT EXISTS FOR (l:Level) ON (l.name);
CREATE INDEX IF NOT EXISTS FOR (resp:Responsibility) ON (resp.name);
CREATE INDEX IF NOT EXISTS FOR (cp:CorePrinciple) ON (cp.name);
CREATE INDEX IF NOT EXISTS FOR (s:Skill) ON (s.name);
CREATE INDEX IF NOT EXISTS FOR (sc:ScopeOfCommunication) ON (sc.name);
CREATE INDEX IF NOT EXISTS FOR (i:Impact) ON (i.name);

// Create Roles
CREATE (:Role {name: 'Data Engineer'});
CREATE (:Role {name: 'Data Analyst'});
CREATE (:Role {name: 'BI Engineer'});
CREATE (:Role {name: 'Machine Learning Engineer'});

// Create Levels
CREATE (:Level {name: 'Junior'});
CREATE (:Level {name: 'Intermediate'});
CREATE (:Level {name: 'Senior'});
CREATE (:Level {name: 'Principal'});

// Create Responsibilities
CREATE (:Responsibility {name: 'Data Pipeline Development'});
CREATE (:Responsibility {name: 'Data Modeling and Optimization'});
CREATE (:Responsibility {name: 'BI Dashboard Development'});
CREATE (:Responsibility {name: 'Data Visualization'});
CREATE (:Responsibility {name: 'Business Reporting'});
CREATE (:Responsibility {name: 'Advanced Analytics'});
CREATE (:Responsibility {name: 'ML Model Development'});
CREATE (:Responsibility {name: 'ML Model Deployment'});
CREATE (:Responsibility {name: 'ML Model Monitoring'});

// Create Core Principles
CREATE (:CorePrinciple {name: 'Data Quality and Integrity'});
CREATE (:CorePrinciple {name: 'Scalability'});
CREATE (:CorePrinciple {name: 'Actionable Insights'});
CREATE (:CorePrinciple {name: 'Model Performance'});
CREATE (:CorePrinciple {name: 'Ethical AI'});

// Create Skills
CREATE (:Skill {name: 'Python'});
CREATE (:Skill {name: 'SQL'});
CREATE (:Skill {name: 'Power BI'});
CREATE (:Skill {name: 'Tableau'});
CREATE (:Skill {name: 'Data Warehousing'});
CREATE (:Skill {name: 'ETL Processes'});
CREATE (:Skill {name: 'Statistics'});
CREATE (:Skill {name: 'Machine Learning'});
CREATE (:Skill {name: 'Deep Learning'});
CREATE (:Skill {name: 'MLOps'});
CREATE (:Skill {name: 'Cloud Platforms'});

// Create Scope of Communication
CREATE (:ScopeOfCommunication {name: 'Engineering Teams'});
CREATE (:ScopeOfCommunication {name: 'Business Stakeholders'});
CREATE (:ScopeOfCommunication {name: 'Executive Leadership'});
CREATE (:ScopeOfCommunication {name: 'Data Science Teams'});

// Create Impact
CREATE (:Impact {name: 'Operational Efficiency'});
CREATE (:Impact {name: 'Data-Driven Decision Making'});
CREATE (:Impact {name: 'Strategic Innovation'});
CREATE (:Impact {name: 'AI-Driven Solutions'});

// Create Role-Level relationships
MATCH (r:Role), (l:Level)
CREATE (r)-[:REQUIRES_LEVEL]->(l);

// Create Role-Responsibility relationships
MATCH (r:Role {name: 'Data Engineer'}), (resp:Responsibility)
WHERE resp.name IN ['Data Pipeline Development', 'Data Modeling and Optimization']
CREATE (r)-[:REQUIRES]->(resp);

MATCH (r:Role {name: 'Data Analyst'}), (resp:Responsibility)
WHERE resp.name IN ['Data Visualization', 'Business Reporting', 'Advanced Analytics']
CREATE (r)-[:REQUIRES]->(resp);

MATCH (r:Role {name: 'BI Engineer'}), (resp:Responsibility)
WHERE resp.name IN ['BI Dashboard Development', 'Business Reporting']
CREATE (r)-[:REQUIRES]->(resp);

MATCH (r:Role {name: 'Machine Learning Engineer'}), (resp:Responsibility)
WHERE resp.name IN ['ML Model Development', 'ML Model Deployment', 'ML Model Monitoring']
CREATE (r)-[:REQUIRES]->(resp);

// Create Role-CorePrinciple relationships
MATCH (r:Role {name: 'Data Engineer'}), (cp:CorePrinciple)
WHERE cp.name IN ['Data Quality and Integrity', 'Scalability']
CREATE (r)-[:FOLLOWS_PRINCIPLE]->(cp);

MATCH (r:Role {name: 'Data Analyst'}), (cp:CorePrinciple {name: 'Actionable Insights'})
CREATE (r)-[:FOLLOWS_PRINCIPLE]->(cp);

MATCH (r:Role {name: 'Machine Learning Engineer'}), (cp:CorePrinciple)
WHERE cp.name IN ['Model Performance', 'Ethical AI', 'Scalability']
CREATE (r)-[:FOLLOWS_PRINCIPLE]->(cp);

// Create Role-Skill relationships
MATCH (r:Role {name: 'Data Engineer'}), (s:Skill)
WHERE s.name IN ['Python', 'SQL', 'Data Warehousing']
CREATE (r)-[:REQUIRES_SKILL]->(s);

MATCH (r:Role {name: 'Data Analyst'}), (s:Skill)
WHERE s.name IN ['SQL', 'Statistics']
CREATE (r)-[:REQUIRES_SKILL]->(s);

MATCH (r:Role {name: 'BI Engineer'}), (s:Skill)
WHERE s.name IN ['SQL', 'Power BI', 'Tableau']
CREATE (r)-[:REQUIRES_SKILL]->(s);

MATCH (r:Role {name: 'Machine Learning Engineer'}), (s:Skill)
WHERE s.name IN ['Python', 'Machine Learning', 'Deep Learning', 'MLOps', 'Cloud Platforms']
CREATE (r)-[:REQUIRES_SKILL]->(s);

// Create Role-ScopeOfCommunication relationships
MATCH (r:Role {name: 'Data Engineer'}), (sc:ScopeOfCommunication {name: 'Engineering Teams'})
CREATE (r)-[:COMMUNICATES_WITH]->(sc);

MATCH (r:Role {name: 'Data Analyst'}), (sc:ScopeOfCommunication {name: 'Business Stakeholders'})
CREATE (r)-[:COMMUNICATES_WITH]->(sc);

MATCH (r:Role {name: 'BI Engineer'}), (sc:ScopeOfCommunication {name: 'Executive Leadership'})
CREATE (r)-[:COMMUNICATES_WITH]->(sc);

MATCH (r:Role {name: 'Machine Learning Engineer'}), (sc:ScopeOfCommunication)
WHERE sc.name IN ['Engineering Teams', 'Data Science Teams', 'Business Stakeholders']
CREATE (r)-[:COMMUNICATES_WITH]->(sc);

// Create Role-Impact relationships
MATCH (r:Role {name: 'Data Engineer'}), (i:Impact {name: 'Operational Efficiency'})
CREATE (r)-[:IMPACTS]->(i);

MATCH (r:Role {name: 'Data Analyst'}), (i:Impact {name: 'Data-Driven Decision Making'})
CREATE (r)-[:IMPACTS]->(i);

MATCH (r:Role {name: 'BI Engineer'}), (i:Impact {name: 'Strategic Innovation'})
CREATE (r)-[:IMPACTS]->(i);

MATCH (r:Role {name: 'Machine Learning Engineer'}), (i:Impact)
WHERE i.name IN ['AI-Driven Solutions', 'Strategic Innovation']
CREATE (r)-[:IMPACTS]->(i);

// Create career progression relationships
MATCH (r1:Role {name: 'Data Analyst'}), (r2:Role {name: 'Data Engineer'})
CREATE (r1)-[:LEADS_TO]->(r2);

MATCH (r1:Role {name: 'BI Engineer'}), (r2:Role {name: 'Data Engineer'})
CREATE (r1)-[:LEADS_TO]->(r2);

MATCH (r1:Role {name: 'Data Analyst'}), (r2:Role {name: 'BI Engineer'})
CREATE (r1)-[:LEADS_TO]->(r2);

// Create initial nodes and relationships can be added here
// Example:
// CREATE (j:Job {id: 'job1', title: 'Software Engineer', location: 'Remote'})
// CREATE (s:Skill {name: 'Python', category: 'Programming'})
// CREATE (c:Company {name: 'Tech Corp'})
// CREATE (j)-[:REQUIRES]->(s)
// CREATE (j)-[:AT]->(c) 