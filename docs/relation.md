[![](https://mermaid.ink/img/pako:eNqdlG1v2jAQgP9K5E9USlFJwkuiaVIb1gIaUrVWmrSAkMGX4DXYmeMUOsp_3yUObDD4sOVTfH783NnnZEsWkgEJSJzK9WJJlbY-f5kIC5_bbV8uXkA1udxZ19cfrXcrz-ha5PhyF0UC1zW_59NpTZ8iYdTgIk6LDZtb7tUlqh9F2ZteSuHuRXd7BNQrlMin6CvMM5rAAfhgCAU_Csi1xaimZUIzHVbr76M-Ruc0h8BaSBHzpF59b6ZbuAG6wsl4Y-KaJnlgcWZnVJlIzCFlGHulaQEBng_VHc9MTY9lzl6WKchBnwjjzez_tO5ei30RAtJTbyEWmkvxr1rvRDv76wiqio-1OQh23tqvrA-N6HmpgLJZKIVWMk1BTa8M8WA6anr-bg2c6EkWgi0UjfG28VyDQPgMi00duH_CT1jFAR20GtGAKramCjdTUhU05psydeUZODXqmmGrHjrVMDxb3jC6fQwts5k609DcuOFRQqQubHAUjTnjWMexZWQsoyNLTe5Nw_ryl61JwBzAfvWlmbq68ChLSGySKM5IENM0B5usQK1oOSbbEpwQzXUKExLg6zN-RRNi1_ElrOo4o-plQiZih7KMim9SrkigVYE6JYtkeZAXGX6D0Oc0UfQ3UjUrxL5oErh-x68kJNiSDQlaTrvpd9q-57g9p4cjm7yRwPOcZq_V9bqe22k7ruftbPKzynrT7Hacm67vI9putbtdtAHjWqqx-X9Vv7HdL47hcfo?type=png)](https://mermaid.live/edit#pako:eNqdlG1v2jAQgP9K5E9USlFJwkuiaVIb1gIaUrVWmrSAkMGX4DXYmeMUOsp_3yUObDD4sOVTfH783NnnZEsWkgEJSJzK9WJJlbY-f5kIC5_bbV8uXkA1udxZ19cfrXcrz-ha5PhyF0UC1zW_59NpTZ8iYdTgIk6LDZtb7tUlqh9F2ZteSuHuRXd7BNQrlMin6CvMM5rAAfhgCAU_Csi1xaimZUIzHVbr76M-Ruc0h8BaSBHzpF59b6ZbuAG6wsl4Y-KaJnlgcWZnVJlIzCFlGHulaQEBng_VHc9MTY9lzl6WKchBnwjjzez_tO5ei30RAtJTbyEWmkvxr1rvRDv76wiqio-1OQh23tqvrA-N6HmpgLJZKIVWMk1BTa8M8WA6anr-bg2c6EkWgi0UjfG28VyDQPgMi00duH_CT1jFAR20GtGAKramCjdTUhU05psydeUZODXqmmGrHjrVMDxb3jC6fQwts5k609DcuOFRQqQubHAUjTnjWMexZWQsoyNLTe5Nw_ryl61JwBzAfvWlmbq68ChLSGySKM5IENM0B5usQK1oOSbbEpwQzXUKExLg6zN-RRNi1_ElrOo4o-plQiZih7KMim9SrkigVYE6JYtkeZAXGX6D0Oc0UfQ3UjUrxL5oErh-x68kJNiSDQlaTrvpd9q-57g9p4cjm7yRwPOcZq_V9bqe22k7ruftbPKzynrT7Hacm67vI9putbtdtAHjWqqx-X9Vv7HdL47hcfo)

# Components
```mermaid
---
title: "Components",
theme: "dark"
---
flowchart LR
    A{Docker.io} --> | spawns | B[[node.js]]
    B --> | serves | E[Webpage]
    A --> | spawns | C[(influxdb 3)]
    A --> | spawns | D[[python3]]
    B <--> | request data | C
    C --> | handles| F[Database: config]
    D --> | spawns |G([Thread_Controller])
    G --> | spawns | H3[Soundcraft Sender]
    G --> | spawns | H2[Soundcraft Listener]
    H2 --> | listen events| H1([Hardware: SouncraftMixer])
    H3 --> | send events | H1
    H2 --> | sends config changes| C
    G --> | spawns| I[APC Thread]
    G --> | spawns| J[MidiMix Thread]
    I --> | changes | H3
    J --> | changes | H3
    I <--> | request config | C
    J <--> | request config | C
```
