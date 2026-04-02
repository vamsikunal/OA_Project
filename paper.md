# Discrete optimization

# Mixed-integer linear programming for project scheduling under various resource constraints

Nicklas Klein, Mario Gnägi, Norbert Trautmann <sup>\*</sup>

Department of Business Administration, University of Bern, Engehaldenstrasse 4, 3012 Bern, Switzerland

![Check for updates button.](1d7527f4316cfe2d342b08d1653d1592_img.jpg)

Check for updates button.

## ARTICLE INFO

### Keywords:

Project scheduling

Mixed-integer linear programming

Resource-constrained project scheduling

Consumption and production of resources

## ABSTRACT

Project scheduling is an important management task in many companies across different industries. Generally, projects require resources, such as personnel or funds, whose availabilities are limited, giving rise to the challenging problem of resource-constrained project scheduling. In this paper, we consider the scheduling of a project consisting of precedence-related activities that require time and two types of resources for execution: storage resources representing, e.g., the project budget; and renewable resources representing, e.g., personnel or equipment. Storage resources are consumed by activities at their start or produced upon their completion, while renewable resources are allocated to activities at their start and released upon their completion. The resource-constrained project scheduling problem with consumption and production of resources (RCPSP-CPR) consists of determining a minimum-makespan schedule such that all precedence relations are respected, the demand for each renewable resource never exceeds its capacity, and the stock level of each storage resource never falls below a prescribed minimum. Due to the consideration of storage resources, the feasibility variant of this problem is NP-complete. We propose a novel compact mixed-integer linear programming (MILP) model based on a novel type of sequencing variables. These variables enable us to identify which activities are processed in parallel and whether a sequencing of activities is necessary to respect the resource capacities. Our computational results indicate that our novel model significantly outperforms state-of-the-art MILP models for all considered scarcity settings of the storage resources. Additionally, our results indicate a superior performance for instances of the well-known resource-constrained project scheduling problem (RCPSP).

## 1. Introduction

A vital aspect of project management is project scheduling, i.e., the allocation of resources to the processing of project activities over time (cf., e.g., Tavares, 2002). If the availability of project resources is limited, this task is referred to as resource-constrained project scheduling (cf., e.g., Brucker et al., 1999). A large portion of the resource-constrained project scheduling literature focuses on renewable resources, which are used by activities while they are in progress and released at completion (e.g., personnel or machinery), and nonrenewable resources, which are consumed by the activities but are not restored (e.g., raw materials). In addition, various researchers have considered the consumption and production of resources (cf., e.g., Carlier & Moukrim, 2015; Carlier et al., 2009; Laborie, 2003; Neumann & Schwindt, 2003). This concept generalizes renewable and nonrenewable resources by assuming that the activities consume a certain quantity of resources at their start or produce a possibly different quantity upon completion. These resources are called storage resources or cumulative resources (cf., e.g., Neumann & Schwindt,

2003). At the project start, for each storage resource, an initial quantity is available for consumption. A typical example of such a resource is a project budget from which the activities require an initial investment or which they increase upon completion. Moreover, storage resources are needed to model utilities built and needed in a manufacturing process (cf., e.g., Agha et al., 2010). A technique that has recently become increasingly relevant for solving project scheduling problems is mixed-integer linear programming (MILP) (cf., e.g., Artigues et al., 2015). The motivation for using MILP for project scheduling is threefold. First, the performance of mathematical programming solvers and computer hardware has improved substantially in recent years; e.g., Koch et al. (2022) report a total speedup factor of up to 1,000 for MILP solvers in the past 20 years. While dedicated exact procedures might still yield better performance, modern solvers can currently solve many problem instances within seconds that earlier versions cannot solve within any reasonable time (cf. Koch et al., 2022). Second, off-the-shelf solvers might be one of the only handy optimization tools available to

<sup>\*</sup> Corresponding author.

E-mail addresses: [nicklas.klein@unibe.ch](mailto:nicklas.klein@unibe.ch) (N. Klein), [mario.gnaegi@unibe.ch](mailto:mario.gnaegi@unibe.ch) (M. Gnägi), [norbert.trautmann@unibe.ch](mailto:norbert.trautmann@unibe.ch) (N. Trautmann).

practitioners. Third, MILP models might offer greater flexibility to represent the dynamically changing characteristics of business applications (e.g., changing objectives or additional project-specific constraints) compared to that of tailored algorithms.

The resource-constrained project scheduling problem with consumption and production of resources (RCPSP-CPR) can be described as follows (cf., e.g., Koné et al., 2013). A set of activities interconnected by completion-start precedence relations is given. For execution, the activities require time and capacities of storage and renewable resources. The RCPSP-CPR consists of determining start times for all activities such that the precedence relations and given renewable resource capacities are respected, and the storage resources' stock never falls below a prescribed minimum level; the objective is to minimize the project completion time, i.e., the makespan, which is typical for, e.g., research and development projects, where the time-to-market is essential. Because storage resources must be considered, determining whether a feasible schedule exists represents an NP-complete decision problem (cf. Carlier & Moukrim, 2015; Carlier et al., 2009).

In the literature, several MILP models have been proposed for the RCPSP-CPR. These models can be divided into two categories: discrete-time (DT) and continuous-time (CT) models. DT models rely on splitting the scheduling horizon into intervals of equal length and allowing activities to start only at the beginning of those intervals. In contrast, CT models allow activities to start at any time during the scheduling horizon. To our knowledge, there are two DT and two CT MILP models for the RCPSP-CPR in the literature. These models were proposed by Koné et al. (2013) and are based on well-established MILP models for the resource-constrained project scheduling problem (RCPSP), which comprises renewable resources only. The authors extend these models to the RCPSP-CPR by including additional variables and constraints to model storage resources. Moreover, Koné et al. (2013) propose novel test sets for the RCPSP-CPR as extensions of benchmark instances for the RCPSP. In their extensive computational study, Koné et al. (2013) compare the performance of the various MILP models for these novel test sets. The results of their computational study indicate that room for improvement remains regarding the number of instances of moderate size that can be solved to optimality in a reasonable time. Furthermore, they did not identify a unique model that performs best for all sets of instances, which is desirable when implementing such a model in practice.

In this paper, we propose a novel continuous-time MILP model for the RCPSP-CPR. The novel model is compact, i.e., it includes a polynomial number of variables and constraints, and is based on two kinds of sequencing variables. The first type is a completion-start sequencing variable that has been used by other CT models in the literature (cf., e.g., Artigues et al., 2003, Trautmann et al., 2018). The second type is a novel start-start sequencing variable that, to our knowledge, is used for the first time to address resource-constrained project scheduling problems. We combine these two types of variables to identify which activities are processed in parallel and, therefore, must not exceed the renewable resource capacities. Furthermore, the combination of these two variable types enables us to track the stock changes of storage resources, and, therefore, the model does not use any additional variables to handle the storage resource constraints. Another advantage of this new variable type is that one can easily interpret its meaning in the problem context, which is important when explaining a solution approach to practitioners or when modeling additional project-specific restrictions. To further enhance the performance of the model, we add valid inequalities to our formulation. While some of these inequalities are based on the completion-start sequencing variables and are known to improve the performance of continuous-time RCPSP models (cf., e.g., Gnägi et al., 2018, Trautmann et al., 2018), we also propose three novel valid inequalities based on the start-start sequencing variables. In our computational study, we first compare the performance of various configurations of our novel model and identify the best setting. Then, we compare our novel model with the four MILP models from the

**Table 1**  
Notation for sets and parameters.

|            |                                                                 |
|------------|-----------------------------------------------------------------|
| $V$        | Set of all activities ( $V = \{0, 1, \dots, n, n+1\}$ )         |
| $E$        | Set of precedence relations $(i, j) \in V \times V$             |
| $TE$       | Transitive closure of $E$                                       |
| $R$        | Set of renewable resources                                      |
| $C$        | Set of storage resources                                        |
| $R_k$      | Capacity of renewable resource $k \in R$                        |
| $C_k$      | Initial stock of storage resource $k \in C$                     |
| $p_i$      | Duration of activity $i \in V$                                  |
| $r_{ik}$   | Demand of activity $i \in V$ of renewable resource $k \in R$    |
| $c_{ik}^-$ | Consumption of activity $i \in V$ of storage resource $k \in C$ |
| $c_{ik}^+$ | Production of activity $i \in V$ of storage resource $k \in C$  |

**Table 2**  
Illustrative example — duration and resource usages.

| $i$ | $p_i$ | $r_{i1}$ | $c_{i2}^-$ | $c_{i2}^+$ |
|-----|-------|----------|------------|------------|
| 1   | 4     | 1        | 3          | 0          |
| 2   | 3     | 1        | 1          | 0          |
| 3   | 2     | 2        | 2          | 0          |
| 4   | 1     | 2        | 1          | 3          |

literature. To analyze the impact on the performance of all models, we examine three scenarios with different levels of storage resource scarcity. In the first scenario, we study the instances proposed by Koné et al. (2013); in these instances, the initial stock of the storage resources can be considered relatively high. In the second scenario, we consider a variant of these instances, in which we have reduced the initial stock. In the third scenario, we investigate another variant of these instances, in which we consider the renewable resources only but not the storage resources, i.e., the same setting as in the RCPSP. In addition, we consider these three scenarios for correspondingly modified instances of the set CV proposed by Coelho and Vanhoucke (2020); with respect to renewable resources, CV instances are considered more challenging to solve than the instances proposed by Koné et al. (2013). Our computational results indicate that our novel model substantially outperforms all reference models and handles the additional challenges of the storage resources best. For all studied instances and scenarios, the novel model solves substantially more instances to feasibility and to optimality than any reference model; in many cases, the reference models struggle to devise feasible project schedules. Notably, our results also indicate that the novel model outperforms the reference models for benchmark instances of the RCPSP of set J30 (cf. Kolisch & Sprecher, 1996) and of set CV (cf. Coelho & Vanhoucke, 2020). Furthermore, we analyze the scalability of the models by using modified instances of set J60 that comprise a relatively large number of activities (cf. Kolisch & Sprecher, 1996). Our results indicate that our novel model scales well toward these larger instances, finding the most proven optimal and best feasible solutions among all models.

The remainder of this paper is structured as follows. In Section 2, we describe the problem setting in detail and provide an illustrative example to highlight the impact of storage resources on the complexity of constructing a feasible project schedule. In Section 3, we review the MILP reference models for the RCPSP-CPR from the literature and briefly summarize the different types of variables used. In Section 4, we explain the novel variable type and our novel MILP model in detail. In Section 5, we present our computational study. In Section 6, we provide some conclusions and provide an outlook on possible future research directions.

## 2. Planning situation

In this section, we describe the RCPSP-CPR in detail and provide an illustrative example of the planning situation. In the remainder of this paper, we use the notation for sets and parameters summarized in Table 1.

![Figure 1: Activity-on-node graph. A directed graph with nodes 0, 1, 2, 3, 4, and 5. Node 0 is the start node with outgoing arcs to nodes 1, 2, and 3. Nodes 1, 2, and 3 have outgoing arcs to node 5. Node 4 has outgoing arcs to nodes 2 and 5.](7055f51feb10ea4ea48b27c36f085286_img.jpg)

Figure 1: Activity-on-node graph. A directed graph with nodes 0, 1, 2, 3, 4, and 5. Node 0 is the start node with outgoing arcs to nodes 1, 2, and 3. Nodes 1, 2, and 3 have outgoing arcs to node 5. Node 4 has outgoing arcs to nodes 2 and 5.

Fig. 1. Illustrative example — activity-on-node graph.

In the RCPSP-CPR, we are given a set of  $n$  real activities. To model the project start and project completion, we additionally consider the two fictitious activities 0 and  $n + 1$ , respectively. We denote the set of all activities as  $V = \{0, 1, \dots, n, n + 1\}$ . Each activity  $i \in V$  has a duration  $p_i$  and requires  $r_{ik}$  units of each renewable resource  $k \in R$  during its execution; i.e., the activity occupies  $r_{ik}$  units while it is in progress and releases them upon its completion. The capacity of renewable resource  $k \in R$  is denoted as  $R_k$ ; i.e., at most  $R_k$  units of the renewable resource can be used simultaneously. For each storage resource  $k \in C$ , the activity consumes  $c_{ik}^-$  units at its start and produces  $c_{ik}^+$  units upon completion. An initial stock  $C_k \geq 0$  that is available at the project start is given for each storage resource  $k \in C$ , and, without loss of generality, we assume the minimum stock level to be zero. We note that storage resources can be considered a generalization of renewable resources: A renewable resource could be modeled as a storage resource whose initial stock is equal to the capacity of the renewable resource and for which each activity produces the amount that it consumes. However, since this is not computationally more efficient, we model renewable resources as a separate resource type in the remainder of this paper. The two fictitious activities 0 and  $n + 1$  have a duration of zero and do not require any resources, i.e.,  $p_i = 0$ ,  $r_{ik} = 0$  ( $k \in R$ ), and  $c_{ik}^- = c_{ik}^+ = 0$  ( $k \in C$ ) for  $i \in \{0, n + 1\}$ . Furthermore, a set of completion-start precedence relations  $E \subseteq V \times V$  is given. For each pair of activities  $(i, j) \in E$ , this precedence relation prescribes that activity  $i$  must be completed before activity  $j$  starts.  $TE$  denotes the transitive closure of these precedence relations; i.e., if  $(i, j) \in E$  and  $(j, h) \in E$ , then the pair  $(i, h)$  is also included in  $TE$ . The RCPSP-CPR consists of determining a start time for each activity such that the total project duration is minimized, all precedence relations are considered, for each renewable resource at each point in time, the total requirement does not exceed its capacity, and for each storage resource, the stock level never falls below zero.

The RCPSP-CPR represents an NP-hard optimization problem as it contains the RCPSP as a special case (cf. Blazewicz et al., 1983). When considering renewable resources only, it is easy to devise a feasible solution. However, when storage resources are involved, determining whether a feasible schedule exists represents an NP-complete decision problem (cf. Carlier & Moukrim, 2015; Carlier et al., 2009).

We illustrate the RCPSP-CPR with an example consisting of  $n = 4$  real activities that require capacities of one renewable resource  $k = 1$  and one storage resource  $k = 2$ , i.e.,  $R = \{1\}$  and  $C = \{2\}$ . The renewable resource has a capacity of  $R_1 = 3$  units, and the initial stock of the storage resource is  $C_2 = 4$ . The project start and the project completion are represented by the two fictitious activities 0 and  $n + 1$ , respectively. The prescribed precedence relations are visualized in the activity-on-node graph in Fig. 1. Each node  $i$  of this graph represents an activity  $i \in V$ , and each arc  $(i, j)$  in this graph represents a precedence relation  $(i, j) \in E$ . The activity durations, renewable resource requirements, and storage resource consumptions and productions are displayed in Table 2.

![Figure 2(a): Usage of the renewable resource. A Gantt chart showing the usage of renewable resource R1 over time t. The y-axis represents the number of units (0 to 3). The x-axis represents time (0 to 7). Activity 3 (duration 2) uses 1 unit from t=0 to t=2. Activity 2 (duration 3) uses 2 units from t=0 to t=3. Activity 4 (duration 1) uses 1 unit from t=2 to t=3. Activity 1 (duration 4) uses 1 unit from t=3 to t=7.](87658d45f2d2f009cbb9cd1079519cb5_img.jpg)

Figure 2(a): Usage of the renewable resource. A Gantt chart showing the usage of renewable resource R1 over time t. The y-axis represents the number of units (0 to 3). The x-axis represents time (0 to 7). Activity 3 (duration 2) uses 1 unit from t=0 to t=2. Activity 2 (duration 3) uses 2 units from t=0 to t=3. Activity 4 (duration 1) uses 1 unit from t=2 to t=3. Activity 1 (duration 4) uses 1 unit from t=3 to t=7.

(a) Usage of the renewable resource

![Figure 2(b): Stock level of the storage resource. A Gantt chart showing the stock level of storage resource C2 over time t. The y-axis represents the stock level (0 to 4). The x-axis represents time (0 to 7). The stock level starts at 4. At t=0, activity 0 starts, consuming 3 units (3-). The stock level drops to 1. At t=2, activity 3 completes, producing 2 units (2+). The stock level rises to 3. At t=3, activity 2 completes, producing 4 units (4+). The stock level rises to 7. At t=3, activity 4 starts, consuming 4 units (4-). The stock level drops to 3. At t=7, activity 1 completes, producing 1 unit (1+). The stock level rises to 4.](9ccd03fe518c562a3fe2d3119f50935e_img.jpg)

Figure 2(b): Stock level of the storage resource. A Gantt chart showing the stock level of storage resource C2 over time t. The y-axis represents the stock level (0 to 4). The x-axis represents time (0 to 7). The stock level starts at 4. At t=0, activity 0 starts, consuming 3 units (3-). The stock level drops to 1. At t=2, activity 3 completes, producing 2 units (2+). The stock level rises to 3. At t=3, activity 2 completes, producing 4 units (4+). The stock level rises to 7. At t=3, activity 4 starts, consuming 4 units (4-). The stock level drops to 3. At t=7, activity 1 completes, producing 1 unit (1+). The stock level rises to 4.

(b) Stock level of the storage resource

Fig. 2. Illustrative example — optimal solution with storage resource.

![Figure 3: Optimal solution without storage resources. A Gantt chart showing the usage of renewable resource R1 over time t. The y-axis represents the number of units (0 to 3). The x-axis represents time (0 to 7). Activity 3 (duration 2) uses 1 unit from t=0 to t=2. Activity 1 (duration 4) uses 1 unit from t=0 to t=4. Activity 2 (duration 3) uses 2 units from t=2 to t=5. Activity 4 (duration 1) uses 1 unit from t=4 to t=5.](50dae0dfbde108cee0040a29f2a42e88_img.jpg)

Figure 3: Optimal solution without storage resources. A Gantt chart showing the usage of renewable resource R1 over time t. The y-axis represents the number of units (0 to 3). The x-axis represents time (0 to 7). Activity 3 (duration 2) uses 1 unit from t=0 to t=2. Activity 1 (duration 4) uses 1 unit from t=0 to t=4. Activity 2 (duration 3) uses 2 units from t=2 to t=5. Activity 4 (duration 1) uses 1 unit from t=4 to t=5.

Fig. 3. Illustrative example — optimal solution without storage resources.

The minimal makespan of this example project is seven; an optimal schedule is depicted in Fig. 2. For each point in time  $t$ , we visualize the usage  $r_1(t)$  of renewable resource  $k = 1$  and stock level  $c_2(t)$  of storage resource  $k = 2$  in Figs. 2(a) and 2(b), respectively.

To illustrate how the storage resource constraints can impact the feasibility of a schedule, we describe how the optimal solution changes if we neglect the storage resource constraints. An optimal solution with the corresponding renewable resource usage  $\bar{r}_1(t)$  is depicted in Fig. 3. To achieve the minimal makespan of five, activity one must start at time zero. However, when starting activity one before activity four is completed, there is no feasible solution for the RCPSP-CPR instance. This stands in contrast to the scheduling problem comprising only renewable resources, where any given order leads to a (potentially suboptimal) feasible solution.

## 3. MILP models from the literature

In this section, we summarize the types of variables that are used in the two DT and the two CT MILP models for the RCPSP-CPR proposed by Koné et al. (2013).

**Discrete-time models.** The DT models for the RCPSP-CPR are based on the DT models for the RCPSP that were introduced by Pritsker et al. (1969) and Christofides et al. (1987). We denote the extended models as DT and DDT, respectively. These two models are very similar; they differ only in their formulation of the precedence relation constraints. We therefore provide a combined explanation for them here. To split the scheduling horizon into intervals of equal length, an upper bound  $T$  on the minimal makespan is needed. For each activity  $i \in V$  and each point in time  $t \in \{0, 1, \dots, T\}$ , the models use a binary variable to indicate whether activity  $i$  starts at time  $t$ . These binary “pulse” variables are used to model the precedence relations and the renewable resource capacities, but they do not provide sufficient information to track the stock changes of the storage resources. Therefore, the models additionally include time-indexed continuous variables for each storage resource to track their available amounts at each point in time. In total, the models use  $\mathcal{O}(T \cdot n)$  binary variables to represent the start times and  $\mathcal{O}(T \cdot |C|)$  additional continuous variables to model the storage resources. Consequently, the total number of variables increases considerably when considering the additional storage resources, especially when the activity durations (and thus the scheduling horizon) are long.

**Continuous-time models.** The first CT model is based on the resource flow model from Artigues et al. (2003) and is denoted as FCT in the following. Both renewable and storage resources are represented as flows that might occur between pairs of activities. Specifically, for each activity pair and each resource, there is a continuous flow variable. Each activity has a minimum total inflow (consumption) and a maximum total outflow (production). The respective initial resource capacities are represented by an outflow of fictitious activity 0. To allow a resource flow from activity  $i$  to activity  $j$ , activity  $i$  must be completed before the start of activity  $j$ . This condition is ensured through a binary completion-start sequencing variable for each pair of activities  $i, j \in V (i \neq j)$  that is equal to one if and only if activity  $i$  is completed before the start of activity  $j$ . Therefore, the FCT model requires  $\mathcal{O}(n^2 \cdot |R|)$  variables for renewable resources and  $\mathcal{O}(n^2 \cdot |C|)$  additional variables for storage resources.

The second CT model, denoted by OOE in the following, is based on the concept of events, particularly the on/off event-based RCPSP model proposed by Koné et al. (2011). In this model, the start of one or more activities is considered an event, which makes the number of activities an upper bound to the number of needed events. For each activity and each event, the model includes a binary variable that indicates whether the activity starts or is still in process at that event. Furthermore, a continuous variable indicates the start time for each event. These variables are sufficient to model the renewable resource constraints. However, additional variables are required to represent the storage resources. Koné et al. (2013) introduce two continuous variables for each activity, event, and storage resource. These variables correspond to the activity’s production (or consumption) of the resource at that event. Moreover, the model includes a continuous variable for each event and each storage resource to track the current stock of the storage resource at the event. Therefore, the OOE model requires  $\mathcal{O}(n^2)$  variables for renewable resources and  $\mathcal{O}(n^2 \cdot |C|)$  additional variables for storage resources.

The order of magnitude of variables and constraints needed for modeling the precedence relations and renewable resources (P-RR) and the additional consideration of the storage resources (add. CPR) are summarized in Table 3. The novel model presented in this paper is the only model that does not require additional variables for the storage resource constraints. Furthermore, the novel model is compact, i.e., the number of variables and constraints can be described by a polynomial in the number of activities and resources.

**Table 3**  
Order of magnitude of variables and constraints in the MILP models.

| Model          | Number of Variables          |                              | Number of Constraints                    |                              |
|----------------|------------------------------|------------------------------|------------------------------------------|------------------------------|
|                | P-RR                         | add. CPR                     | P-RR                                     | add. CPR                     |
| DT             | $\mathcal{O}(T \cdot n)$     | $\mathcal{O}(T \cdot  C )$   | $\mathcal{O}(T \cdot  R  + n^2)$         | $\mathcal{O}(T \cdot  C )$   |
| DDT            | $\mathcal{O}(T \cdot n)$     | $\mathcal{O}(T \cdot  C )$   | $\mathcal{O}(T \cdot  R  + n^2 \cdot T)$ | $\mathcal{O}(T \cdot  C )$   |
| FCT            | $\mathcal{O}(n^2 \cdot  R )$ | $\mathcal{O}(n^2 \cdot  C )$ | $\mathcal{O}(n^3 + n^2 \cdot  R )$       | $\mathcal{O}(n^2 \cdot  C )$ |
| OOE            | $\mathcal{O}(n^2)$           | $\mathcal{O}(n^2 \cdot  C )$ | $\mathcal{O}(n^3 + n \cdot  R )$         | $\mathcal{O}(n^2 \cdot  C )$ |
| Novel CT model | $\mathcal{O}(n^2)$           | 0                            | $\mathcal{O}(n^2 + n \cdot  R )$         | $\mathcal{O}(n \cdot  C )$   |

**Table 4**  
Variables used in the novel MILP model.

| Variable | Description                                                                                                                                  |
|----------|----------------------------------------------------------------------------------------------------------------------------------------------|
| $S_i$    | Start time of activity $i$                                                                                                                   |
| $y_{ij}$ | $\begin{cases} = 1, & \text{if activity } i \text{ is completed before the start of activity } j \\ = 0, & \text{otherwise} \end{cases}$     |
| $z_{ij}$ | $\begin{cases} = 1, & \text{if activity } i \text{ starts before or at the same time as activity } j \\ = 0, & \text{otherwise} \end{cases}$ |

## 4. Novel MILP model

In this section, we introduce the novel continuous-time MILP model for the RCPSP-CPR. In Section 4.1, we introduce the variables used, including the novel type of sequencing variables. In Section 4.2, we present the model in detail. In Section 4.3, we first transfer some well-known valid inequalities from the literature to the model, and then, we add some valid inequalities that we can formulate by using the novel sequencing variables.

### 4.1. Variables used in the novel MILP model

As is common for CT models, we use a continuous variable  $S_i$  for each activity  $i \in V$  to indicate the respective start time. To model both types of resource constraints, at the start of each activity, we determine which activities have already been completed and which activities are currently in progress. For this purpose, we introduce two types of binary sequencing variables for certain pairs of activities. The first type is denoted as  $y_{ij}$  ( $i, j \in V : i \neq j$ ), with  $y_{ij} = 1$  if activity  $i$  is completed at any time before or at the same time as activity  $j$  starts and  $y_{ij} = 0$  otherwise. This variable is called a completion-start sequencing variable and is also used to model the completion-start precedence relations. The second type is the novel start-start sequencing variable, denoted as  $z_{ij}$  ( $i, j \in V : i \neq j, (i, j) \notin TE, (j, i) \notin TE$ ), with  $z_{ij} = 1$  if activity  $i$  starts at any time before or at the same time as activity  $j$  starts and  $z_{ij} = 0$  otherwise. Since the sequencing is prespecified for any pair of activities that have a given precedence relation, we do not include the variables  $z_{ij}$  and  $z_{ji}$  for any pair of activities  $(i, j) \in TE$ . At the start of any activity  $i$ , we can then determine whether another activity  $j$  is already completed ( $z_{ji} = y_{ji} = 1$ ), is currently in progress ( $z_{ji} = 1, y_{ji} = 0$ ), or has not yet been started ( $z_{ji} = y_{ji} = 0$ ). We summarize the notations for the variables used in Table 4.

We explain the novel variable type by using the example from Section 2; the values of the variables for all real activities in the optimal solution (cf. Fig. 2) are displayed in Fig. 4. At the start of, e.g., activity four, for each other activity, we check whether it has already been completed, is currently in progress, or has not yet started. Activity two has already been started ( $z_{24} = 1$ ) but is not completed ( $y_{24} = 0$ ), i.e., it is in progress at the start of activity four. Therefore, we must consider its renewable resource requirement and storage resource consumption in combination with activity four. Since there is a precedence relation between activities three and four ( $(3, 4) \in E$ ), activity three is already completed ( $y_{34} = 1$ ); therefore, we do not have to consider its renewable resource requirement. However, we must account for the difference between storage resource consumption and production to determine the currently available stock of storage resources. Activity one has not yet

![Figure 4: Illustrative example — values of the variables in the optimal solution. The figure shows a Gantt chart with four activities (1, 2, 3, 4) over a time horizon t from 0 to 7. Activity 1 (S1=0) starts at t=3 and ends at t=7. Activity 2 (S2=0) starts at t=0 and ends at t=3. Activity 3 (S3=2) starts at t=0 and ends at t=2. Activity 4 (S4=5) starts at t=2 and ends at t=3. The chart includes various variables like z_ij, y_ij, and r_1(t) plotted against time t.](7a3561af571faf036baa93f5f4b1bdb9_img.jpg)

Figure 4: Illustrative example — values of the variables in the optimal solution. The figure shows a Gantt chart with four activities (1, 2, 3, 4) over a time horizon t from 0 to 7. Activity 1 (S1=0) starts at t=3 and ends at t=7. Activity 2 (S2=0) starts at t=0 and ends at t=3. Activity 3 (S3=2) starts at t=0 and ends at t=2. Activity 4 (S4=5) starts at t=2 and ends at t=3. The chart includes various variables like z\_ij, y\_ij, and r\_1(t) plotted against time t.

Fig. 4. Illustrative example — values of the variables in the optimal solution.

been started ( $z_{14} = 0$ ) and is hence not completed ( $y_{14} = 0$ ); therefore, we do not have to consider its renewable resource requirements and storage resource consumption or production.

### 4.2. Novel MILP model

In this subsection, we describe the novel CT model in detail. The objective is to minimize the project makespan, i.e., the start of fictitious activity  $n + 1$ .

$$\min. S_{n+1} \quad (1)$$

Constraints (2) ensure that the start of activity  $j$  occurs after the completion of activity  $i$  if the completion-start sequencing variable  $y_{ij}$  is set to one. Hereby, the constant  $T$  represents the scheduling horizon, i.e., an upper bound on the minimal makespan; we set  $T := \sum_{i \in V} p_i$ .

$$S_i + p_i \leq S_j + T(1 - y_{ij}) \quad (i, j \in V : i \neq j) \quad (2)$$

Together with constraints (2), constraints (3) enforce the precedence relations.

$$y_{ij} = 1, \quad y_{ji} = 0 \quad ((i, j) \in TE) \quad (3)$$

Constraints (4) assure that the novel start-start sequencing variables are set according to the timing variables  $S_i$ , i.e.,  $z_{ij}$  being equal to one if  $S_i \leq S_j$ . Therefore, we need a sufficiently small parameter  $\epsilon > 0$  to set both variables  $z_{ij}$  and  $z_{ji}$  equal to one if activities  $i$  and  $j$  start at the same time. If all activity durations are integer values, we can set  $\epsilon := 1$ .

$$T \cdot z_{ij} \geq S_j - S_i + \epsilon \quad (i, j \in V : i \neq j, (i, j) \notin TE, (j, i) \notin TE) \quad (4)$$

Constraints (5) model the storage resource constraints. At the start of each activity  $i$ , we check whether there is sufficient stock remaining for the resource consumption of this activity. The left-hand side of the constraint represents the consumption of activity  $i$  plus the total consumption for all activities that are still in progress at the start of activity  $i$ . More precisely, we consider the resource consumption of each other activity  $j$  that starts at any time before activity  $i$  or at the same time as activity  $i$  but is not completed before activity  $i$  begins. This condition is fulfilled for activity  $j$  if and only if the term  $z_{ji} - y_{ji}$  is equal to one. The right-hand side of the equation corresponds to the initial stock of the storage resource plus the net production of all completed activities, i.e.,  $c_{jk}^+ - c_{jk}^-$  for each activity  $j$ , where  $y_{ji}$  is equal to one. This outcome represents the amount of storage resources that are available

for consumption for all activities that are still in progress when activity  $i$  starts.

$$c_{ik}^- + \sum_{\substack{j \in V, j \neq i \\ (i, j), (j, i) \notin TE}} c_{jk}^- (z_{ji} - y_{ji}) \leq C_k + \sum_{j \in V, j \neq i} y_{ji} (c_{jk}^+ - c_{jk}^-) \quad (i \in V, k \in C : c_{ik}^- > 0) \quad (5)$$

For renewable resources, only the resource requirement of all activities  $j$  being executed in parallel to activity  $i$  must be considered; therefore, the analogous constraint reads

$$r_{ik} + \sum_{\substack{j \in V, j \neq i \\ (i, j), (j, i) \notin TE}} r_{jk} (z_{ji} - y_{ji}) \leq R_k \quad (i \in V, k \in R : r_{ik} > 0) \quad (6)$$

The model for the RCPSP-CPR without extensions (NE) then reads as follows:

$$\left\{ \begin{array}{l} \min. \quad S_{n+1} \\ \text{s.t.} \quad (2)–(6) \\ \text{(SEQ\_NE)} \quad \left\{ \begin{array}{ll} S_i \in \mathbb{R}_{\geq 0} & (i \in V) \\ y_{ij} \in \{0, 1\} & (i, j \in V : i \neq j) \\ z_{ij} \in \{0, 1\} & (i, j \in V : i \neq j, (i, j) \notin TE, (j, i) \notin TE) \end{array} \right. \end{array} \right.$$

### 4.3. Extended MILP models

In this subsection, we add various valid inequalities that further enhance the performance of the model. We consider the set

$$F_2 := \{(i, j) \in V : i < j, (i, j), (j, i) \notin TE, \exists k \in R : r_{ik} + r_{jk} > R_k\}$$

of tuples of activities that cannot be executed simultaneously because the total requirement of the activities exceeds the capacity of any renewable resource. For each of these tuples, at least one of the corresponding completion-start sequencing variables must be equal to one, i.e.,

$$y_{ij} + y_{ji} \geq 1 \quad ((i, j) \in F_2) \quad (7)$$

If a precedence relation is given between the activities of such a tuple, the corresponding sequencing variable is forced to be one, and therefore these tuples must not be considered. Analogously, for set

$$F_3 := \{(i, j, h) \in V : i < j < h, (i, j), (i, h), (j, h) \notin F_2, \\ (i, j), (j, i), (i, h), (h, i), (j, h), (h, j) \notin TE, \\ \exists k \in R : r_{ik} + r_{jk} + r_{hk} > R_k\},$$

the inequality

$$y_{ij} + y_{ji} + y_{ih} + y_{hi} + y_{jh} + y_{hj} \geq 1 \quad ((i, j, h) \in F_3) \quad (8)$$

must be fulfilled.

Additionally, activity  $i$  cannot be completed before the start of activity  $j$  if activity  $j$  is completed before the start of activity  $i$ , i.e.,

$$y_{ij} + y_{ji} \leq 1 \quad (i, j \in V : i < j, (i, j) \notin TE, (j, i) \notin TE) \quad (9)$$

It is known from the literature that inequalities (7), (8), and (9) improve the performance of continuous-time MILP models for the RCPSP (cf., e.g., Trautmann et al., 2018, Gnägi et al., 2018, Koné et al., 2011). Our novel model with these extensions from the literature (EL) reads as follows:

$$\text{(SEQ\_EL)} \begin{cases} \min. & S_{n+1} \\ \text{s.t.} & (2)–(9) \\ & S_i \in \mathbb{R}_{\geq 0} \quad (i \in V) \\ & y_{ij} \in \{0, 1\} \quad (i, j \in V : i \neq j) \\ & z_{ij} \in \{0, 1\} \quad (i, j \in V : i \neq j, (i, j) \notin TE, (j, i) \notin TE) \end{cases}$$

In addition to these known inequalities, which are based on the completion-start sequencing variables only, we propose three novel valid inequalities that are based on the novel start-start sequencing variables. First, we note that for any pair of activities, at least one activity has to start before the other or both activities must start at the same time, i.e.,

$$z_{ij} + z_{ji} \geq 1 \quad (i, j \in V : i < j, (i, j) \notin TE, (j, i) \notin TE) \quad (10)$$

Constraints (11) model the fact that if activity  $i$  is completed before the start of activity  $j$ , activity  $i$  also has to start before  $j$ .

$$z_{ij} \geq y_{ij} \quad (i, j \in V : i \neq j, (i, j) \notin TE, (j, i) \notin TE) \quad (11)$$

If both variables  $z_{ij}$  and  $z_{ji}$  are equal to one for a pair of activities  $i, j \in V$ , then these two activities must start at the same time, i.e.,

$$2 - z_{ij} - z_{ji} \geq \frac{1}{T}(S_i - S_j) \quad (i, j \in V : i \neq j, (i, j) \notin TE, (j, i) \notin TE) \quad (12)$$

Our fully extended model (EF) then reads as follows:

$$\text{(SEQ\_EF)} \begin{cases} \min. & S_{n+1} \\ \text{s.t.} & (2)–(12) \\ & S_i \in \mathbb{R}_{\geq 0} \quad (i \in V) \\ & y_{ij} \in \{0, 1\} \quad (i, j \in V : i \neq j) \\ & z_{ij} \in \{0, 1\} \quad (i, j \in V : i \neq j, (i, j) \notin TE, (j, i) \notin TE) \end{cases}$$

## 5. Computational results

In this section, we report on our computational analysis. In Section 5.1, we describe our experimental design. In Section 5.2, we analyze various configurations of our novel model to study the impact of the model extensions presented in Section 4.3 and to identify the best configuration. In Section 5.3, we compare the performance of our novel model to state-of-the-art models from the literature (cf. Table 5); thereby, we analyze three scenarios for the storage resources. In the first scenario, we study the instances proposed by Koné et al. (2013) that comprise storage resources with a relatively high initial stock. In the second scenario, we investigate the same instances but with a reduced initial stock of storage resources. Due to this reduced initial stock, the storage resources are scarcer, which makes it more challenging to devise feasible solutions for these instances. In the third scenario, we consider renewable resources only. In Section 5.4, we consider the same three scenarios for modified instances of set CV that are considered hard to solve regarding renewable resources (cf. Coelho & Vanhoucke, 2020). In Section 5.5, we analyze the scalability of the models using modified instances of set J60 that comprise a relatively large number of activities (cf. Kolisch & Sprecher, 1996).

### 5.1. Experimental design

In this subsection, we describe our experimental design. In Section 5.1.1, we outline the test instances. In Section 5.1.2, we describe the performance measures used. In Section 5.1.3, we report on the details of the implementation.

#### 5.1.1. Test instances

We used two instance sets to analyze the influence of the storage resources on the performance of the models. The first set is called J30-CPR and contains 456 instances for which a feasible solution exists. Koné et al. (2013) generated this set by modifying benchmark instances for the RCPSP from set J30 of the PSPLIB (Kolisch & Sprecher, 1996). Set J30 contains 480 problem instances comprising 30 real activities and four renewable resources. To extend the set to the RCPSP-CPR, Koné et al. (2013) added three storage resources to the instances by assigning randomly generated integer values between zero and ten to each activity for each storage resource. They set the initial stock of each storage resource to a value based on a so-called resource strength indicator  $RS^{\text{CPR}} \in [0, 1]$ , with a lower value implying that the storage resources are scarcer. The authors sampled this indicator randomly from the interval  $[0.7, 1]$ , implying that the initial stock of the storage resource constraints is relatively high. Therefore, the storage resources are not very scarce in this set of instances. To analyze instances that are more challenging regarding the storage resources, we modify the J30-CPR instances by lowering the initial stock of the storage resources. We achieve this by randomly sampling the resource strength indicator from the interval  $[0.4, 0.7]$ . The resulting set contains 290 instances for which a feasible solution exists; we call it J30-CPR-L.

The second set is called CV-CPR and contains 623 instances for which a feasible solution exists. We generated this set by modifying benchmark instances for the RCPSP from set CV, which was proposed by Coelho and Vanhoucke (2020). Set CV contains 623 problem instances comprising 20 to 30 real activities and one to four renewable resources. The problem instances of this set are considered very hard to solve. To extend the set to the RCPSP-CPR, we added three storage resources to the instances following the methodology proposed by Koné et al. (2013). We randomly sampled the resource strength indicator from the empirical values of set J30-CPR, implying a relatively high initial stock of the storage resource constraints. Again, we modify these instances by reducing the storage resources' initial stock by randomly sampling a new resource strength indicator from the interval  $[0.4, 0.7]$ . The resulting set contains 617 instances for which a feasible solution exists; we call it CV-CPR-L.

To analyze the scalability of all models, we use a set called J60-CPR that contains 476 instances for which a feasible solution exists. We generated this set by modifying benchmark instances for the RCPSP from set J60 of the PSPLIB (Kolisch & Sprecher, 1996). Set J60 contains 480 problem instances comprising 60 real activities and four renewable resources. Again, we added three storage resources to the instances following the methodology proposed by Koné et al. (2013). We generated the initial stock using the same resource strength indicators as the corresponding J30-CPR instances, e.g., instance J60\_1\_1 received the same resource strength indicator as instance J30\_1\_1.

We summarize the characteristics of all sets of instances in Table 6, where we indicate whether the instances comprise renewable resources (RR), storage resources with a relatively high initial stock (CPR), or a relatively low initial stock (CPR-L). Additionally, we indicate in which subsection the results for the respective set of instances are discussed. Note that the results for instances comprising renewable resources only, i.e., instances of the RCPSP, are discussed in Section 5.3.3 and Section 5.4.3.

#### 5.1.2. Performance measures

For all sets of instances, we report the following key metrics:

**Table 5**  
Overview of model abbreviations.

| Abbreviation | DT | CT | Variable type | Proposed by        | Based on                   |
|--------------|----|----|---------------|--------------------|----------------------------|
| DT           | x  |    | Pulse         | Koné et al. (2013) | Pritsker et al. (1969)     |
| DDT          | x  |    | Pulse         | Koné et al. (2013) | Christofides et al. (1987) |
| FCT          |    | x  | Flow          | Koné et al. (2013) | Artigues et al. (2003)     |
| OOE          |    | x  | Event         | Koné et al. (2013) | Koné et al. (2011)         |
| SEQ          |    | x  | Sequence      | This paper         | This paper                 |

**Table 6**  
Overview of the sets of instances.

| Name      | RR | CPR | CPR-L | Results       |
|-----------|----|-----|-------|---------------|
| J30-CPR   | x  | x   |       | Section 5.3.1 |
| J30-CPR-L | x  |     | x     | Section 5.3.2 |
| J30       | x  |     |       | Section 5.3.3 |
| CV-CPR    | x  | x   |       | Section 5.4.1 |
| CV-CPR-L  | x  |     | x     | Section 5.4.2 |
| CV        | x  |     |       | Section 5.4.3 |
| J60-CPR   | x  | x   |       | Section 5.5   |

**Table 7**  
Overview of the model configurations.

| Abbreviation | Valid constraints | Integer start times |
|--------------|-------------------|---------------------|
| SEQ_NE       | None              | x                   |
| SEQ_EL       | (7) – (9)         | x                   |
| SEQ_EF       | (7) – (12)        | x                   |
| SEQ          | (7) – (12)        | ✓                   |

- # Feas: Number of instances for which a feasible solution was found
- # Opt: Number of instances for which a proven optimal solution was found
- # Best: Number of instances for which the best feasible solution among all models was found
- Gap<sup>MIP</sup>: Average relative deviation between the objective function value of the best feasible solution (UB\*) and the best lower bound (LB\*), calculated as (UB\* – LB\*)/UB\*
- Gap<sup>UB\*–CPM</sup><sub>A</sub>: Average relative deviation between UB\* and the lower bound based on the critical path method (CPM), calculated as (UB\* – CPM)/CPM; this average considers the subset of instances for which all models have found a feasible solution.
- Gap<sup>UB\*–CPM</sup><sub>M</sub>: Average relative deviation between UB\* and CPM; this average considers all instances for which the respective model has found a feasible solution.
- Gap<sup>LB\*–CPM</sup>: Average relative deviation between LB\* and CPM, calculated as (LB\* – CPM)/CPM
- Time: Average time (in seconds) used to build the model and solve an instance

In all following tables, we mark the best values per metric in bold. As the metric Gap<sup>UB\*–CPM</sup><sub>M</sub> uses different subsets of instances for all models, it is not suitable for a comparison between models, but rather serves as a benchmark for the overall solution quality. Therefore, we do not mark any values in this column in bold.

#### 5.1.3. Implementation

We implemented all models in Python 3.8 and used Gurobi version 9.1.2 as the MILP solver. We carried out the computations on a workstation with two 8-core Intel(R) Xeon(R) E5-2687 W CPUs (3.1 GHz) and 128 GB RAM. We set a time limit of 500 seconds per instance and restricted the number of available threads to two. Since the duration of all activities in the considered sets of instances takes integer values, we set  $\epsilon := 1$  in constraints (4) for our novel model. Additionally, this implies that there is at least one optimal solution where the start times of all activities are integers. This allows us to restrict the start time variables of all CT models to take integer values. We demonstrate the benefit of this restriction in Section 5.2. Apart from this modification, we implemented all reference models as described in Koné et al. (2013), using  $T = \sum_{i \in V} p_i$  as the scheduling horizon.

### 5.2. Model configuration

In this subsection, we analyze the computational performance of various configurations of the novel CT model. Specifically, we analyze

the impact of various sets of valid constraints and of restricting the timing variables to take integer values. We list our configurations in Table 7.

We use the instances of set J30-CPR for this comparison. The results are summarized in Table 8.

We observe a positive impact of both sets of valid constraints on the model performance regarding all metrics. In particular, the lower bounds are improved, which is indicated by the larger gap to the critical path-based lower bound. Additionally, restricting the start time variables to take integer values has a positive influence, leading to configuration SEQ performing best regarding all metrics. Therefore, we use the SEQ configuration of our novel model for all of the following experiments. For the CT reference models FCT and OOE, we also restrict the start time variables to take integer values in the following.

### 5.3. Results for set J30-CPR and variants

In this subsection, we present the computational results for the instances of sets J30-CPR (cf. Section 5.3.1), J30-CPR-L (cf. Section 5.3.2), and J30 (cf. Section 5.3.3).

#### 5.3.1. Relatively high initial stock

In this subsection, we report our computational results for the instances of set J30-CPR; the results are presented in Table 9.

We observe that our novel model (SEQ) performs best regarding all comparable metrics. It yields the best feasible solution among all models to all instances and proves optimality for over 97% of them. Additionally, it yields the best upper and lower bounds, on average. Regarding the models from the literature, model FCT performs best, providing a feasible solution to each instance, solving the second-most instances to optimality, and providing a best solution among all models for the second-most instances. This result stands in contrast to the results of Koné et al. (2013), where both DT models provide proven optimal solutions for more instances than the FCT model. This improved performance can be attributed to restricting the start time variables to integer values. The DT models provide the third-highest number of instances solved to optimality. However, they cannot find a feasible solution for 22 and 24 instances, respectively. The OOE model finds feasible solutions to the third-most instances but cannot prove optimality for any instance. A reason for this might be the weaker LP relaxation that the model yields, whose optimal objective function values are smaller than the CPM lower bound for most instances; this is also the reason for the negative value in the Gap<sup>LB\*–CPM</sup> column.

#### 5.3.2. Relatively low initial stock

In this subsection, we report our computational results for the instances of set J30-CPR-L and discuss the influence of the relatively

**Table 8**  
Comparison of different model configurations using the instances of set J30-CPR.

| Model  | # Feas | # Opt | # Best | Gap <sup>MIP</sup> | Gap <sup>UB<sup>b</sup>-CPM</sup> <sub>A</sub> | Gap <sup>UB<sup>b</sup>-CPM</sup> <sub>M</sub> | Gap <sup>LB<sup>b</sup>-CPM</sup> | Time         |
|--------|--------|-------|--------|--------------------|------------------------------------------------|------------------------------------------------|-----------------------------------|--------------|
| SEQ_NE | 454    | 386   | 403    | 3.23%              | 17.90%                                         | 17.90%                                         | 12.47%                            | 97.20        |
| SEQ_EL | 456    | 414   | 428    | 1.23%              | 17.27%                                         | 17.67%                                         | 15.66%                            | 73.61        |
| SEQ_EF | 456    | 438   | 451    | 0.64%              | 17.04%                                         | 17.43%                                         | 16.31%                            | 40.51        |
| SEQ    | 456    | 445   | 455    | <b>0.38%</b>       | <b>17.01%</b>                                  | 17.39%                                         | <b>16.73%</b>                     | <b>22.74</b> |

**Table 9**  
Computational results for the instances of set J30-CPR.

| Model | # Feas | # Opt | # Best | Gap <sup>MIP</sup> | Gap <sup>UB<sup>b</sup>-CPM</sup> <sub>A</sub> | Gap <sup>UB<sup>b</sup>-CPM</sup> <sub>M</sub> | Gap <sup>LB<sup>b</sup>-CPM</sup> | Time         |
|-------|--------|-------|--------|--------------------|------------------------------------------------|------------------------------------------------|-----------------------------------|--------------|
| DT    | 434    | 379   | 392    | 1.79%              | 14.53%                                         | 17.12%                                         | 14.71%                            | 122.12       |
| DDT   | 432    | 381   | 396    | 1.15%              | 14.06%                                         | 15.22%                                         | 15.29%                            | 133.36       |
| FCT   | 456    | 411   | 436    | 1.22%              | 13.57%                                         | 17.54%                                         | 15.60%                            | 84.84        |
| OOE   | 453    | 0     | 66     | 86.38%             | 23.88%                                         | 28.28%                                         | -83.10%                           | 501.87       |
| SEQ   | 456    | 445   | 456    | <b>0.38%</b>       | <b>13.50%</b>                                  | 17.39%                                         | <b>16.73%</b>                     | <b>22.74</b> |

**Table 10**  
Computational results for the instances of set J30-CPR-L.

| Model | # Feas | # Opt | # Best | Gap <sup>MIP</sup> | Gap <sup>UB<sup>b</sup>-CPM</sup> <sub>A</sub> | Gap <sup>UB<sup>b</sup>-CPM</sup> <sub>M</sub> | Gap <sup>LB<sup>b</sup>-CPM</sup> | Time         |
|-------|--------|-------|--------|--------------------|------------------------------------------------|------------------------------------------------|-----------------------------------|--------------|
| DT    | 205    | 139   | 155    | 4.18%              | 20.23%                                         | 27.58%                                         | 22.39%                            | 315.44       |
| DDT   | 203    | 138   | 156    | 3.48%              | 21.69%                                         | 25.06%                                         | 24.19%                            | 338.45       |
| FCT   | 269    | 167   | 208    | 5.68%              | 20.09%                                         | 31.09%                                         | 22.44%                            | 280.41       |
| OOE   | 261    | 0     | 2      | 88.76%             | 42.07%                                         | 53.36%                                         | -83.25%                           | 502.22       |
| SEQ   | 290    | 259   | 287    | <b>1.66%</b>       | <b>19.20%</b>                                  | 31.99%                                         | <b>29.36%</b>                     | <b>94.22</b> |

**Table 11**  
Computational results for the instances of set J30.

| Model | # Feas | # Opt | # Best | Gap <sup>MIP</sup> | Gap <sup>UB<sup>b</sup>-CPM</sup> <sub>A</sub> | Gap <sup>UB<sup>b</sup>-CPM</sup> <sub>M</sub> | Gap <sup>LB<sup>b</sup>-CPM</sup> | Time         |
|-------|--------|-------|--------|--------------------|------------------------------------------------|------------------------------------------------|-----------------------------------|--------------|
| DT    | 480    | 443   | 462    | 0.77%              | 13.44%                                         | 13.59%                                         | 12.21%                            | 54.16        |
| DDT   | 479    | 437   | 451    | 1.00%              | 13.66%                                         | 13.66%                                         | 11.96%                            | 67.89        |
| FCT   | 480    | 458   | 473    | 0.69%              | 13.30%                                         | 13.45%                                         | 12.23%                            | 40.21        |
| OOE   | 480    | 0     | 302    | 81.46%             | 15.35%                                         | 15.50%                                         | -79.38%                           | 501.08       |
| SEQ   | 480    | 471   | 478    | <b>0.35%</b>       | <b>13.28%</b>                                  | 13.43%                                         | <b>12.80%</b>                     | <b>15.28</b> |

low initial stock on the performance of the models. The results of our analysis for set J30-CPR-L are summarized in Table 10.

Again, the novel CT model performs best regarding all comparable metrics; it finds the best solution among all models for most instances and proves optimality for over 89% of the instances. Additionally, it yields the best upper and lower bounds, on average. Regarding the models from the literature, again, the FCT model performs best. However, none of the models from the literature finds feasible solutions to all instances. When comparing the results to the previous setting with a relatively high initial stock, the model SEQ devises feasible solutions to all instances in both settings. In contrast, all models from the literature provide feasible and proven optimal solutions to relatively fewer instances than in the previous setting. In summary, it can be stated that the performance advantage of the novel CT model over the reference models from the literature increases with the scarcity of storage resources.

#### 5.3.3. No storage resources

In this subsection, we report our computational results for the instances of set J30 and discuss the influence of omitting the storage resources on the performance of the models for these instances. The results of our computational study for set J30 are presented in Table 11.

We observe that our novel model performs best regarding all metrics, providing proven optimal solutions to over 98% of instances. Regarding the models from the literature, all models provide feasible solutions to all instances, except for DDT, which fails to find a feasible solution to one instance. This stands in contrast to both of the previous settings that include storage resources. Additionally, the average quality of their upper and lower bounds is considerably better for the models from the literature. This highlights that these models are not best suited to tackle the additional challenges the storage resource constraints pose. A potential explanation for this is that the SEQ model

does not require additional variables to tackle the storage resource constraints. Nevertheless, these results indicate that the SEQ model also outperforms the reference models for instances without storage resources, i.e., instances of the RCPSP.

### 5.4. Results for set CV-CPR and variants

In this subsection, we report on the computational results for the instances of sets CV-CPR (cf. Section 5.4.1), CV-CPR-L (cf. Section 5.4.2), and CV (cf. Section 5.4.3).

#### 5.4.1. Relatively high initial stock

In this subsection, we report our computational results for the instances of set CV-CPR. The results are presented in Table 12.

We observe that our novel model (SEQ) performs best regarding the number of instances solved to optimality and the number of instances for which a best solution among all models has been obtained. Additionally, it yields the best upper bounds, on average. Regarding the models from the literature, FCT and OOE find feasible solutions to all instances, while the models DT and DDT do not find feasible solutions to 11 and 59 instances, respectively. However, the DT and DDT models yield better lower bounds than all CT models. Therefore, they have smaller MIP gaps, on average.

#### 5.4.2. Relatively low initial stock

In this subsection, we report on our computational results for the instances of set CV-CPR-L and discuss the influence of the relatively low initial stock on the performance of the models. The results of our computational study for set CV-CPR-L are presented in Table 13.

Again, we observe that our novel model performs best regarding the number of instances solved to optimality and the number of instances for which a best feasible solution among all models has been obtained.

**Table 12**  
Computational results for the instances of set CV-CPR.

| Model | # Feas     | # Opt     | # Best     | Gap <sup>MIP</sup> | Gap <sub>A</sub> <sup>UB<sup>+</sup>-CPM</sup> | Gap <sub>M</sub> <sup>UB<sup>+</sup>-CPM</sup> | Gap <sup>LB<sup>+</sup>-CPM</sup> | Time          |
|-------|------------|-----------|------------|--------------------|------------------------------------------------|------------------------------------------------|-----------------------------------|---------------|
| DT    | 612        | 29        | 284        | <b>13.35%</b>      | 149.09%                                        | 153.27%                                        | <b>118.91%</b>                    | 483.55        |
| DDT   | 564        | 22        | 187        | 14.94%             | 155.49%                                        | 156.53%                                        | 116.14%                           | 492.96        |
| FCT   | <b>623</b> | 16        | 243        | 36.55%             | 149.59%                                        | 153.10%                                        | 56.54%                            | 497.92        |
| OOE   | <b>623</b> | 0         | 21         | 90.90%             | 163.28%                                        | 167.09%                                        | –76.36%                           | 501.54        |
| SEQ   | <b>623</b> | <b>62</b> | <b>447</b> | 29.54%             | <b>145.92%</b>                                 | 149.23%                                        | 70.48%                            | <b>472.69</b> |

**Table 13**  
Computational results for the instances of set CV-CPR-L.

| Model | # Feas     | # Opt     | # Best     | Gap <sup>MIP</sup> | Gap <sub>A</sub> <sup>UB<sup>+</sup>-CPM</sup> | Gap <sub>M</sub> <sup>UB<sup>+</sup>-CPM</sup> | Gap <sup>LB<sup>+</sup>-CPM</sup> | Time          |
|-------|------------|-----------|------------|--------------------|------------------------------------------------|------------------------------------------------|-----------------------------------|---------------|
| DT    | 605        | 25        | 298        | <b>13.07%</b>      | 149.29%                                        | 151.92%                                        | <b>118.90%</b>                    | 485.55        |
| DDT   | 549        | 24        | 172        | 15.34%             | 157.91%                                        | 158.31%                                        | 115.72%                           | 493.09        |
| FCT   | <b>617</b> | 25        | 280        | 35.49%             | 149.96%                                        | 152.26%                                        | 58.94%                            | 494.65        |
| OOE   | <b>617</b> | 0         | 21         | 92.32%             | 165.17%                                        | 168.11%                                        | –79.68%                           | 501.56        |
| SEQ   | <b>617</b> | <b>52</b> | <b>404</b> | 30.42%             | <b>147.77%</b>                                 | 149.97%                                        | 69.89%                            | <b>474.09</b> |

**Table 14**  
Computational results for the instances of set CV.

| Model | # Feas     | # Opt     | # Best     | Gap <sup>MIP</sup> | Gap <sub>A</sub> <sup>UB<sup>+</sup>-CPM</sup> | Gap <sub>M</sub> <sup>UB<sup>+</sup>-CPM</sup> | Gap <sup>LB<sup>+</sup>-CPM</sup> | Time          |
|-------|------------|-----------|------------|--------------------|------------------------------------------------|------------------------------------------------|-----------------------------------|---------------|
| DT    | <b>623</b> | 35        | <b>398</b> | <b>11.28%</b>      | <b>147.74%</b>                                 | 147.63%                                        | <b>119.83%</b>                    | 477.84        |
| DDT   | <b>623</b> | 5         | 249        | 14.00%             | 152.33%                                        | 152.20%                                        | 116.13%                           | 499.23        |
| FCT   | 622        | 27        | 249        | 34.16%             | 151.10%                                        | 151.10%                                        | 61.36%                            | 493.82        |
| OOE   | <b>623</b> | 0         | 47         | 85.50%             | 159.95%                                        | 159.83%                                        | –62.92%                           | 500.84        |
| SEQ   | <b>623</b> | <b>77</b> | 357        | 29.04%             | 149.05%                                        | 148.94%                                        | 72.72%                            | <b>465.87</b> |

Additionally, it yields the best upper bounds, on average. Regarding the models from the literature, FCT and OOE find feasible solutions to all instances, while DT and DDT do not find feasible solutions to 12 and 68 instances, respectively. Again, the DT and DDT models yield better lower bounds and therefore have smaller MIP gaps, on average. When comparing the results to the previous setting with a relatively high initial stock, we observe that the CT models find feasible solutions to all instances in both settings. Surprisingly, the DDT and FCT models solve more instances to optimality than in the previous setting, which stands in contrast to their performance regarding the instances of set J30-CPR-L. However, the novel model still solves more instances to optimality and finds the best feasible solution among all models for more instances.

#### 5.4.3. No storage resources

In this subsection, we report our computational results for the instances of set CV and discuss the influence of omitting the storage resources on the models' performance for these instances. The results of our computational study for set CV are presented in Table 14.

We observe that our novel model performs best regarding the number of instances solved to optimality, providing optimal solutions to more than twice as many instances as the second-best model regarding this metric (DT). Regarding the models from the literature, all models find feasible solutions to all instances, except for FCT, which fails to devise a feasible solution to one instance. The DT model finds the best feasible solution among all models for most instances and, on average, yields the best upper and lower bounds. This stands in contrast to both of the previous settings that include storage resources, where the models DT and DDT models did not devise feasible solutions to all instances.

In sum, the SEQ model performs best regarding the number of instances solved to feasibility and optimality. In the settings without storage resources, the DT model yields better upper bounds, on average, and more instances for which a best solution among all models has been obtained. This result is notable, since the DT model was originally proposed by Pritsker et al. (1969) over 50 years ago and still performs comparably well today, especially when only renewable resources are involved.

### 5.5. Scalability

In this subsection, we analyze the scalability of all models regarding instances that comprise a relatively large number of activities. The results of our computational study for set J60-CPR are presented in Table 15.

We observe that our novel model (SEQ) provides optimal solutions for most instances, and for over 90% of the instances, it provides the best solution among all models. Regarding the models from the literature, the OOE model solves the most instances to feasibility, missing only three instances. However, the solution quality is considerably worse than that of all other models. The DT and DDT models do not find feasible solutions to 91 and 121 instances, respectively. This also explains their relatively small MIP gaps that are calculated by using only instances for which the respective model found a feasible solution. Notably, the FCT model, which performed second-best in the J30-CPR instances, only provides feasible solutions to less than 40% of the instances. One potential explanation for this is that the model comprises  $O(n^3)$  constraints and, therefore, does not scale well to instances comprising a relatively large number of activities.

In sum, the novel model provides many feasible solutions that have a comparably low makespan, while the models from the literature struggle with finding feasible solutions, indicating that our novel model scales best to larger instances.

## 6. Conclusion and outlook

In this paper, we introduced a novel continuous-time MILP model for the RCPSP-CPR based on a novel type of sequencing variable. By combining completion-start sequencing variables with this novel type of start-start sequencing variable, we can efficiently formulate renewable resource and storage resource constraints. The main advantages of our model are that it does not require additional variables to model the storage resource constraints, it is compact, and the variables are easily interpretable. In addition, the novel variable type enables us to add novel valid inequalities to the model that considerably enhance its computational performance. Our computational results indicate that our model outperforms all reference MILP models from the literature and is best suited to address the additional challenges the storage resource constraints pose.

**Table 15**  
Computational results for the instances of set J60-CPR.

| Model | # Feas | # Opt      | # Best     | Gap <sup>MIP</sup> | Gap <sup>UB<sup>A</sup>-CPM</sup> | Gap <sup>UB<sup>M</sup>-CPM</sup> | Gap <sup>LB<sup>A</sup>-CPM</sup> | Time          |
|-------|--------|------------|------------|--------------------|-----------------------------------|-----------------------------------|-----------------------------------|---------------|
| DT    | 385    | 353        | 370        | 1.22%              | <b>1.16%</b>                      | 4.51%                             | <b>5.20%</b>                      | 152.21        |
| DDT   | 355    | 332        | 333        | <b>0.72%</b>       | 1.34%                             | 2.23%                             | 3.65%                             | 238.88        |
| FCT   | 187    | 128        | 132        | 4.79%              | 5.32%                             | 8.88%                             | 1.91%                             | 437.10        |
| OOE   | 473    | 0          | 27         | 97.38%             | 62.54%                            | 81.19%                            | –95.42%                           | 510.62        |
| SEQ   | 450    | <b>372</b> | <b>438</b> | 3.45%              | <b>1.16%</b>                      | 9.32%                             | 4.09%                             | <b>124.80</b> |

For future research, we propose to develop a matheuristic solution procedure, i.e., a mathematical programming-based heuristic, that utilizes the new MILP model. A promising direction may be to initially relax the binary restriction on the sequencing variables, and afterwards iteratively restore it (cf., e.g., [Bigler et al., 2024](#)). Furthermore, how the new modeling approach can be adapted to related project scheduling problems, i.e., variants of the RCPSP that have been proposed in the literature (cf., e.g., [Hartmann & Briskorn, 2022](#) for an overview), should be investigated.