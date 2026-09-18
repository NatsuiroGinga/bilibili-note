---
title: "2026-Garcia-Slips-Behavioral-Evidence-Aggregation"
date: 2026-09-03
tags:
  - 类型/全文转换
  - "attack-detection"
source_pdf: "raw/papers/attack-detection/2026-Garcia-Slips-Behavioral-Evidence-Aggregation.pdf"
---

> 本文件由 `tools/pdf_to_fulltext.sh`（`mineru-open-api extract`）机械批量转换生成，用于全文检索与细节复查；不是 `SCHEMA.md`「类型/论文」要求的结构化理解笔记（无背景/方法核心/我的理解等分节）。原件中的图片按 `wiki/AGENTS.md` 的规定未落库（不保存 PDF 转换中间文件），正文中的图片引用链接可能失效。

# Slips: Behavioral Evidence Aggregation for Network Security

Sebastian Garcia sebastian.garcia@agents.fel.cvut.cz Faculty of Electrical Engineering, Czech Technical University in Prague Czechia

Ondřej Lukáš ondrej.lukas@aic.fel.cvut.cz Faculty of Electrical Engineering, Czech Technical University in Prague Czechia

David Otta do.dipl.strat@gmail.com Faculty of Electrical Engineering, Czech Technical University in Prague Czechia

Veronica Valeros valerver@fel.cvut.cz Faculty of Electrical Engineering, Czech Technical University in Prague Czechia

Martin Řepa repa.martin@protonmail.ch Recon Wave Czechia

František Střasák frenky.strasak@gmail.com Faculty of Electrical Engineering, Czech Technical University in Prague Czechia

Dita Hollmannová holl.dita@gmail.com Independent Researcher Czechia

Alya Gomaa alyaggomaa@gmail.com Faculty of Electrical Engineering, Czech Technical University in Prague Czechia

Lukáš Forst lukas.forst@gmail.com Recon Wave Czechia

Jan Svoboda svobo114@fel.cvut.cz Faculty of Electrical Engineering, Czech Technical University in Prague Czechia

## Abstract

Network intrusion detection systems often analyze individual pack ets or flows, although malicious behavior may develop across many connections and over time. This may limit their ability to combine isolated detections into a coherent assessment of host behavior. Packet-level features may also be too low-level for complex AI based detection, requiring additional processing to improve accuracy while maintaining a low false-positive rate.

We present Slips, a network intrusion detection system that builds host-centered behavioral profiles and organizes activity into time windows. It uses a modular architecture in which independent modules report evidence rather than generating final alerts directly. Slips then accumulates this evidence into host-level decisions. We evaluate Slips against Suricata on an expert-labeled PCAP dataset. At the profile-time-window level, Slips achieved 83% higher recall and a 70% higher F1 score than Suricata, while neither system produced false positives. These results indicate that time-windowbased evidence accumulation can produce context-aware decisions that better align with expert judgment.

## CCS Concepts

• Security and privacy → Intrusion detection systems; Network security; • Computing methodologies → Supervised learning; Neural networks.

## Keywords

intrusion detection, behavioral analysis, machine learning, evidence ensemble, recurrent neural networks

## 1 Introduction

Network intrusion detection systems (NIDSs) often analyze individual packets, flows, or protocol events to decide whether activity is malicious. However, malicious behavior may develop across many connections and over time. This leaves NIDSs with limited context for deciding when individual suspicious events indicate that a host is behaving maliciously [17, 31].

For example, several failed connection attempts to diferent ports may be insuficient to determine whether they constitute a port scan. Similarly, command-and-control trafic may be characterized by the periodicity of a sequence of flows rather than by the content of just a single packet [17]. An accurate detection requires a balance between low-level flow detections and high-level behavioral analysis.

Intrusion detection systems have been studied and deployed for decades, with mature taxonomies, architectures, and operational tools spanning host- and network-based detection, signatures, anomaly detection, and stateful protocol analysis [8, 40]. Snort and Suricata perform stateful packet and stream inspection and can apply thresholds within individual rules [34, 40]. Zeek converts trafic into protocol events that scripts can relate across connections [38], while systems such as Kitsune maintain online trafic statistics for an anomaly model [28].

Graph-based and alert-correlation systems aggregate activity or detector outputs into higher-level reports [11, 48]. Existing architectures therefore provide some type of state, aggregation, or correlation, but do not combine all three elements presented by our proposal: a shared behavioral profile for each host using time windows, a common representation for evidence produced by diverse detectors, a modularized architecture with many modules and a host-level decision that preserves links to the trafic supporting it. We compare these architectural diferences in Section 6.

We describe Slips [4], first created in 2012[6], a modern modular network security system that uses individual detections to analyze host behavior over time. Although Slips consumes network trafic and performs intrusion detection and prevention, its architecture is closer to a Security Orchestration, Automation, and Response (SOAR) system than to an IDS [32]. It collects and normalizes net work observations, maintains shared state, correlates findings from diverse modules, exports to diferent systems, makes a higher-level decision, and can act back on the network to stop an attack.

Slips models each IP address as a behavioral profile divided into configurable time windows. AI and non-AI modules contribute evidence about the profile’s flows, protocol events, and derived behavior; Slips accumulates this evidence before raising alerts and preserves the contributing detections and supporting flows for accountability, as described in Section 2.1.

This paper focuses on Slips’ core architecture, how organizing detections by profile and time window improves detection, and how low-level detections are combined into alerts when suficient evidence is available.

To evaluate Slips, we conducted two sets of experiments, de scribed in Section 3. First, we ran Slips and Suricata on three PCAP files containing port scans of diferent sizes and durations (100, 1000, and 65,536 ports). The goal of this experiment is to evaluate whether each IDS can identify basic scan-related behavior, how Slips accumulates evidence before raising an alert, and what level of activity is required before each system reports it. A port scan is one of the most basic activities that an IDS should detect, yet to this day, it remains surprisingly dificult to achieve correctly.

Second, we ran Slips and Suricata on three diferent PCAP files, two malicious (Bladabindi RAT and TrickBot) and one benign (social media trafic on Windows 7), and evaluated the performance metrics of each system using the expert-labeled ground-truth log files for each PCAP. These experiments use two comparison modes: flow-by flow, which supports the way Suricata works, and profile-window, which supports the way Slips works. The goal of this experiment is to compare signature-based Suricata with behavioral- and time window-based Slips in terms oftheir detection performance metrics.

Results of the port scan experiments show that Slips generates scan-related evidence for all three scan captures. It confirms that Slips separates the generation of intermediate evidence from the final alerting: suspicious behavior can be recognized and stored without being escalated immediately. Suricata did not recognize any of the three port scans and raised no alerts.

Results from the malware and benign experiments show that Slips achieved stronger detection performance than Suricata across both evaluation modes, while maintaining a very low false-positive rate. In the flow-by-flow mode comparison, Slips achieved an F1 score of0.1603 compared with 0.0033 for Suricata, with both systems producing the same false-positive rate of 0.000025. In the profile window view, Slips achieved an F1 score of 0.3268, compared with 0.1925 for Suricata, and both systems produced zero false positives. These results suggest that accumulating evidence across behavioral profiles and time windows can improve host-level decision-making while avoiding unnecessary alerts from isolated detections.

This paper makes seven contributions.

(1) Modular architecture for network security analysis in which detectors, ML models, exports, and responses are connected through shared behavioral states.

(2) A description of host profiles based on time windows as the main analysis entity.

(3) An adaptive evidence ensemble method in which diverse modules, including an online ML flow classifier and a multiflow ML recurrent model, produce accountable evidence as behavior evolves, and of how Slips accumulates that evidence into host-level alerts.

(4) A mechanism that allows end users to adapt and extend the training of ML models using their own trafic.

(5) Organization-level whitelisting that allows users to exclude alerts and block requests to or from domains, IPs, and certificates across multiple protocols.

(6) Comparison between Slips and Suricata using PCAP files from the IDSEVAL dataset.

(7) New dataset to evaluate IDS systems, including a new labeling framework and a new performance comparison tool.

## 2 Slips System Overview

The core Slips architecture, shown in Figure 1, consists of four major parts that are continually running in parallel: (1) input processing and profiling, (2) detection modules, (3) evidence ensembling and alerting, and (4) active response and exporting.

In the input processing and profiling part, described in Section 2.1, network trafic enters through the input process in various formats, such as PCAP and Zeek logs, among others. The profiler then converts the input trafic into a common internal flow format, creates the host profiles and time windows, stores the resulting records in the database, and dispatches the flows to the modules using a pub/sub architecture.

In the detection modules part, described in Section 2.2, each module analyzes the input data to generate evidence. Evidence is a detection related to one or more flows.

In the evidence ensembling part, described in Section 2.3, the evidence handler receives evidence from each module, filters it using the whitelist, and enriches it. When suficient evidence accumulates in the ensemble, the evidence handler raises an alert and may request an active response.

In the active response and exporting part, described in Section 2.4, the blocking module blocks the detected attacker through the firewall, isolates the local-network attacker using ARP poisoning, and exports alerts.

## 2.1 Input Normalization and Profiling

Slips can ingest packets from network interfaces and many network trafic formats, including PCAP and PCAP-NG [20, 47], Zeek logs [46], Suricata EVE logs [35], Argus BinetFlow binary logs [44], and nfdump flows [18].

Packet captures and live trafic are processed by a Zeek process controlled by Slips and then ingested, while the rest of the input formats are specifically parsed. All input are converted to a unique common flow format for all modules.

In the case of using a network interface or PCAP file, Slips uses an extended Zeek with eleven custom scripts that add fields and logs, including: JA3 and JA3S TLS fingerprints [41], ARP events, ICMP scan events, DNS-over-HTTPS signals, SHA256 file hashes, network gateway information, IRC protocol, and TELNET, rlogin, and rsh login records.

![](images/2a85fcfb9fc161ab394cce7e2aff64b8b322d7cd0fd689309fffaa3292abeb9c.jpg)  
Figure 1: Core Slips architecture. (1) Network inputs are nor malized into a common flow format and aggregated into host profiles and time windows. (2) Detection modules analyze the input data to emit evidence. (3) Evidence is analyzed as an ensemble, and alerts are decided. (4) Responses are executed, and data is exported. Redis provides a pub/sub ar chitecture for communication between parts and for runtime data, while SQLite provides persistent storage.

After the input data is processed, the profiler code creates a behavioral profile structure for each observed source IP address and partitions its activity into time windows (by default, 1 hour). This means that each profile-time-window (from now on, just profile) groups all the activity of that source IP. This lets Slips analyze behavior as a continuous process rather than just treating a host as infected or not. New flows are assigned to the profile by times tamp, including late or out-of-order arrivals. A profile, therefore, represents host behavior over time rather than a single connection.

Slips input processing can operate in two analysis-direction modes: out and both. The out mode answers the question "Is my computer infected and communicating maliciously?" by storing only outgoing connections from each profile. The both mode answers the question "Is my computer also being attacked?", by storing both outgoing and incoming connections on each profile.

2.1.1 Threat Intelligence. Slips includes a feed update manager that periodically downloads, normalizes, and refreshes several types of threat intelligence (TI) feeds. These include malicious JA3 and JA3S fingerprints, SSL certificate fingerprints, Tor exit nodes, the Tranco top benign domains [24], and 42 public TI feeds<sup>1</sup>. The data are used as blacklists or whitelists, and also enrich IP addresses referenced in evidence.

The IP info module, described later, also adds metadata to each IP address, including ASN, geolocation city (using GeoLite DBs), WHOIS data, domain creation date, domain registrant information, and MAC address vendor. It also uses a heuristic to infer the local gateway’s IP and MAC addresses. Lookups run asynchronously alongside modules, and the retrieved metadata are attached to the corresponding evidence before reporting. All feeds and auxiliary databases are locally cached and refreshed periodically by configuration.

2.1.2 Whitelists. Slips supports user-defined and built-in whitelists to reduce context-dependent false positives and suppress known benign activity. For example, trafic from an internal monitoring server may resemble scanning but be expected in a particular net work.

User-Defined Whitelist. Each whitelist entry specifies an indicator type, value, direction, and ignore mode. Supported indicator types are IP addresses, domains, MAC addresses, and organizations. The direction determines whether the entry applies to the flow source, destination, or both, while the ignore mode allows ignoring the entry for flows, alerts, or both.

In flow-ignoring mode, Slips drops matching flows before enrichment, detection, storage, and display in the web interface. This reduces processing overhead and removes known benign trafic from the analyst’s view. However, information from these flows is unavailable to later detections. For example, whitelisting a DNS server in this mode prevents Slips from learning its role and hides its trafic from the interface.

In alert-ignoring mode, matching flows remain available for enrichment, detection, and display, but their evidence and alerts are suppressed. Any generated evidence is discarded before alert accumulation and, therefore, cannot trigger an alert or blocking request. For each evidence item, Slips checks both the attacker and victim against whitelisted IP addresses, DNS resolution answers, queried domains, CNAMEs, TLS SNI values, URLs, and MAC addresses.

Organization-aware whitelisting is a novel feature of Slips that extends conventional IP and domain-based whitelists. Slips allows users to whitelist entire organizations by putting their names, such as Google, Microsoft, Apple, Facebook, and Twitter. Slips expands these organizations by querying their known domains, IP ranges, and ASNs.

A user can whitelist trafic associated with an organization and configure whether matching flows, alerts, or both are suppressed. This helps remove known benign organizational trafic from the analyst’s view and keeps attention focused on more relevant activ ity.

Built-In Whitelist. In addition to user-defined entries, Slips optionally can use the top 10,000 domains from the Tranco list, a daily ranking of the one million most popular websites [24]. The feed update manager downloads and caches the list daily. This list helps prevent false positives involving well-known destinations. For example, a domain flagged by a threat-intelligence source may be ignored when it belongs to a known whitelisted organization such as Google.

Tranco domains are whitelisted only at the alert level: related flows remain available for processing and inspection, but their evidence is suppressed and does not contribute to alerts.

## 2.2 Detection Modules

Slips currently has 24 independent modules, including behavioral and ML-based detectors. Each module runs as a separate process and has access to both Redis and SQLite through a shared database interface. Each module registers in the Redis channels for the type of flows that it needs, for example, DNS Request.

Each detection module focuses on a specific behavioral family and emits evidence when it finds suspicious activity. Evidence is a detection that may include one or more flows and is sent to the evidence handler rather triggering a response.

Most modules use heuristic behavioral and adaptive rules rather than stateless ones. They maintain a state for each profile and time window, and update their detections as new events arrive. As a result, their decisions depend on the number and timing of related events, rather than on a fixed property of a single packet or flow.

Detection modules can be enabled, disabled, or added from the configuration file, and some modules allow individual detections to be disabled without disabling the entire module. Based on their purpose, detection modules are grouped into behavioral, peer-topeer, machine-learning, defense, and export modules.

Each evidence generated by a module must have a threat level (Info, Low, Medium, High, and Critical) and confidence (from 0 to 1). The Info threat level indicates they are worth reporting, but do not pose a direct threat so they don’t count towards the alert score. Critical evidence contributes significantly to the score required to generate an alert.

2.2.1 Behavioral Modules. Behavioral modules analyze specific network protocols to detect suspicious activity. They cover both single-event anomalies (e.g., malformed or unexpected protocol use) and adaptive, event-count-based behaviors (e.g., scans and brute-force attacks).

Flow Alerts. The Flow Alerts module is a dispatcher for a collection of protocol-specific analyzers. It consumes normalized flow records and selected Zeek logs for DNS, TLS/SSL, SSH, SMTP, tun nels, software, Zeek notices, and remote login activity (e.g., Telnet, rlogin, and rsh), as well as information from downloaded-file logs.

This module contains the majority of Slips detections. It flags long connections, unknown destination ports, repeated rejected connections, repeated Telnet attempts, data uploads, TOR exit-node connections, and connections made without a prior DNS resolution.

Several Flow Alert detections adapt their behavior based on event counts. For example, repeated rejected connections, repeated Telnet attempts, SMTP brute-force, bursts of NXDOMAIN replies, and repeated empty HTTP connections are evaluated based on the events accumulated for the profile within the time window. These detections, therefore, depend on the number and timing of related events, not on any single flow.

For DNS flows, the Flow Alerts module detects young domains, DNS answers with high-entropy TXT records, private IPs in DNS answers, many NXDOMAIN replies that may indicate DGA behavior, ARPA scans, and DNS resolutions that are not followed by a connection.

For TLS/SSL flows, it detects self-signed certificates, malicious JA3 or JA3S fingerprints, certificate common-name mismatches, suspicious organization names in certificates, DNS-over-HTTPS, large Pastebin downloads, and non-SSL trafic on port 443.

For SSH flows, it detects successful SSH logins. It uses Zeek’s auth\_success field when available; otherwise, it estimates success from the total bytes exchanged.

For SMTP flows, it detects invalid SMTP logins and SMTP bruteforce attempts based on Zeek fields.

It also detects GRE tunnels and GRE scans, multiple uses of SSH client or server versions, malicious TLS/SSL certificates from downloaded files, and login events from Zeek’s login.log.

ARP. The ARP module detects attacks and abnormal ARP behavior in the local network. It raises evidence for:

• ARP scans, when one host sends ARP requests to at least five diferent IP addresses within 30 seconds,

• ARP packets sent outside the configured local network, and

• Unsolicited ARP replies.

The ARP scan detector is adaptive over a short time interval: one ARP request is normal, but a burst of requests to several diferent addresses within 30 seconds is treated as discovery behavior.

It also checks for MITM ARP attacks. If the same MAC address was previously linked to one IP and later appears to claim another IP, Slips raises evidence of a possible ARP cache poisoning attack.

Brute-force Detector. The brute-force detector focuses on detecting SSH brute forcing. It is adaptive: for each source profile, time window, destination IP, and destination port, it aggregates failed SSH sessions and authentication attempts into a campaign. When the number of failed logins reaches the configured threshold, Slips raises password-guessing evidence. After the threshold is reached, it does not emit the same evidence for every new attempt; instead, it reports again only at sparse, bucketed points as the campaign grows. Confidence increases with the number of attempts and reaches full confidence after a larger number.

The module also uses SSH client banners. Tools and libraries such as Hydra, Medusa, and Ncrack are purpose-built for automated authentication testing, while Paramiko and libssh enable programmatic SSH sessions [15, 26, 33, 37, 49]. Their presence, therefore, increases the confidence used in the evidence.

HTTP Analyzer. The HTTP analyzer checks HTTP-specific behavior and raises evidence for:

• Suspicious user agents, abrupt user-agent changes per profile, and mismatches between the user-agent OS and the MAC vendor,

• Executable downloads inferred from HTTP response MIME types,

• Repeated empty HTTP connections to common sites (a pat tern that can be consistent with malware checking internet connectivity) [29],

• Large Pastebin downloads above a configured size thresh old,

• Unknown HTTP methods reported by Zeek’s weird.log,

• Established TCP trafic on port 80 that Zeek did not classify as HTTP.

Leak Detector. The leak detector searches packet captures for sen sitive data patterns and runs only when Slips analyzes a PCAP. It ap plies YARA rules shipped with the module (including GPS-location leak patterns) [51]. When a rule matches, Slips uses tshark [52] to extract the source and destination IPs, protocol, ports, and timestamp, and reports them as evidence.

Network Discovery. The network discovery is an adaptive module that detects scanning and probing behavior. It raises evidence for:

• vertical port scans (one source contacting many ports on the same destination IP using non-established TCP or UDP flows),

• horizontal port scans (one source contacting the same port on many destination IPs),

• ICMP sweeps reported by Zeek notices (including timestamp scans, address scans, and address-mask scans), and

• DHCP scans, when a client requests four or more diferent IP addresses in the same time window.

The main problem of detecting port scans is that tools can not generate a new alert for each new port scanned, but also they need to show the diference between scanning 5 ports and 65,536. Therefore, Slips uses a logarithmic scale to detect port scans: it emits evidence when the scan grows enough to cross a new threshold of behavior, rather than setting an evidence for every small increase. The confidence is determined by the volume of supporting trafic, so the evidence score increases as more packets and destinations are observed.

2.2.2 Peer-to-Peer. Slips is the first IDS to implement a peer-topeer network of detectors both in the local network and globally on the Internet by using the libP2P library. If two computers with Slips are on the same local network, they will find each other and start sharing data. The goal is to share detection information so as to better protect each other.

To protect privacy, Slips peers only share the attacker’s IP address or domain, threat score, and confidence value, rather than full trafic or contextual data.

Local P2P and Local Trust. The local P2P module enables Slips instances on the same network to ask each other for an IP address and to share detections. The module queries local peers, waits briefly for responses, aggregates peer scores using a trust model, and stores the resulting network opinion.

Slips raises evidence when the aggregated peer opinion indicates that the IP is suspicious. In addition to queries, the local P2P module receives blame reports when another peer blocks an attacker. The local trust model is inspired by the trust model of the Sality P2P botnet [14]: trust depends on good communication and on how long peers have known each other, with peers unable to influence the trust other peers have in them because each peer computes trust locally rather than asking others for it. This is crucial to avoid adversarial peers manipulating the network.

Global P2P and Global Trust. Slips also has a global P2P module that implements three DNS-based supernodes on the Internet, allowing every public Slips instance to automatically share and receive threat intelligence. It also allows organizations to define their own private feed of peers using cryptographic signatures.

Peers respond with an opinion represented as a score and confidence. To avoid blindly trusting adversarial responses, Slips applies a trust model, aggregates peer reports, and then caches the final network opinion. As with local P2P, shared information is minimal and does not include full evidence contents or private flow details.

2.2.3 Machine Learning and AI. The ML modules in Slips are a crucial and hard part to maintain, since the models are continually retrained using our own datasets and pipelines. Before publication, we compare many models in large datasets to decide which model to ship. ML modules operate at two levels: an online linear classifier to detect individual flows, and a bidirectional gated recurrent unit (GRU) to detect command-and-control behavior. Both models are free, open, and distributed with Slips.

Flow-Level ML Detection. The flow-level ML detection module applies a pre-trained SGDClassifier and StandardScaler to each eligible normalized flow. The shipped model is trained on our own curated collection of security datasets, including the public Security Datasets for Testing collection [7]. The module removes unused fields, excludes protocols without the required port-based representation, encodes transport protocol and connection state, and uses port, duration, packet-count, and byte-count features.

During normal operation (test mode), flows are analyzed individually, and only high-confidence detections are sent as evidence. Since the diference between the training datasets and the user’s trafic is usually high, the default threat level is low, and confidence is also low at 0.1.

More importantly, the module allows end users to extend the ML model locally using their own trafic. This module implements a type of transfer learning for this purpose. The user can set the learning mode in the configuration to train and the default label to normal or malicious, and then run Slips normally. The userdefined label is then applied to the flows, and the module continues training the shipped model with the new data. The updated classifier and scaler are stored on disk. By switching the mode back to test the user can now use an extended and probably better model.

This mechanism transfers a model trained on distributed data to the operator’s local environment without requiring a separate ML pipeline or model replacement. Technically, it is an incremental supervised adaptation of a linear model, rather than neural transfer learning through frozen and fine-tuned layers. This is the first time, as far as we know, of a ML model that allows the end user to adapt it locally.

Recurrent Command-and-Control Detection. The ML command and-control detection module analyzes behavior across network flows to detect command-and-control channels. For each profile, the module receives flows that are aggregated by the source IP address, destination IP address, destination port, and protocol. All these flows, aggregated, form a tuple that represents the behavior of the source IP towards a specific service. Slips converts each flow in this tuple into a letter (e.g., ’a’), which discretizes the flow duration, size and periodicity (relative to flows). An additional letter is used to encode the elapsed time since the previous flow $\left( \mathrm { e . g . , } ^ { \ 3 \cdot 5 } \right)$ . The resulting string of letters is analyzed by the module’s ML model in search of well-known behavioral patterns in command and control channels.

The current model is a bidirectional GRU distributed as a pretrained Keras model [12, 42]. The shipped model is trained on our own curated collection of security datasets, including the public Security Datasets for Testing [7].

A command-and-control detection requires a model score greater than 0.99. Confidence is not the raw model score: it grows with ob served sequence length as min(�/100, 1), where � is the number of encoded characters, so short matches contribute less than behavior supported by a longer history.

When the threshold is crossed, the module creates evidence with a high threat level (0.8) and reports the flow that triggered the evaluation with the evidence. Each item then enters the ensemble for its own profile and time window. The GRU therefore detects a multi-flow temporal pattern.

2.2.4 Exporting Modules. Slips provides exporting modules that exchange IoCs, evidence, and alerts with external systems. Internally, Slips records each evidence item and alert as JSON in the IDMEFv2 [25] format in alerts.json. Evidence items are repre sented as IDMEFv2 Event objects, while alerts are represented as IDMEFv2 Incident objects. In addition to this internal representa tion, Slips can export alerts to external platforms in several formats, including STIX over TAXII [22, 23], CESNET Warden [9], and Slack notifications.

Exporting Alerts Module. The exporting alerts module sends Slips evidence and alerts to external systems.

It supports exporting alerts to Slack and sending STIX-formatted evidence to TAXII servers. Slack alerts are posted to a configured Slack channel through a bot token, while STIX export converts evidence into STIX indicators before transmitting them to the configured TAXII server.

CESNET Module. The CESNET module shares alerts with the Warden servers operated by the CESNET organization [9]. When CESNET export is enabled, the module converts evidence into the IDEA0 format [10] and sends it to a Warden server. Informational evidence and evidence about local IP addresses are not exported. The module can also receive alerts from Warden servers, convert them into threat intelligence data, and use them as a blacklist for future detections.

## 2.3 Evidence Ensemble and Alerting

Slips combines evidence from diferent detection methods. It does not average model probabilities or require its detectors to share features. Instead, every rule, ML model, behavioral detector, and threat-intelligence module converts its result into an evidence object and sends it to the evidence handler process for processing. Each evidence item includes the detection type, attacker, and optional victim, profile, time window, threat level, confidence, timestamp, detection method (e.g., AI or behavioral), relevant protocol and ports, and identifiers of the supporting flows. Related evidence can also be linked.

The evidence handler validates each new evidence item before it is accumulated. It applies the configured whitelist and ignores informational evidence when computing the score. Evidence can still be logged, exported, or shared independently of whether it raises the accumulated score.

For decision-making, Slips maps low, medium, high, and critical threat to 0.2, 0.5, 0.8, and 1.0, respectively. Evidence � contributes $s _ { i } ~ = ~ t _ { i } c _ { i }$ , where $t _ { i }$ is this threat value and $c _ { i } \in [ 0 , 1 ]$ is detector confidence. The ensemble score for profile $\mathcal { P }$ and time window � is $\begin{array} { r } { S _ { p , w } = \sum _ { i } s _ { i } } \end{array}$ over eligible evidence assigned to that profile and window. Informational evidence contributes zero, whitelisted evidence is removed, and evidence already used in a previous alert is not counted again.

When $S _ { p , w }$ reaches the configured alert threshold, the handler creates an alert containing the profile, time window boundaries, accumulated score, and identifiers of all contributing evidence. Thus, a high-confidence GRU detection can contribute strongly, a lowconfidence or flow-level ML result contributes less, and several independent ML and non-ML findings can jointly cross the threshold. No individual model is allowed to make the final alerting decision on its own.

This separation creates three explicit semantic levels. Flows and protocol events are observations; evidence is a module’s accountable interpretation of one or more observations; and an alert is the system’s combined decision about a host over a period. The links among these levels allow an analyst or a downstream system to reconstruct which modules contributed, how strongly, and which trafic supports the alert.

## 2.4 Active Response and Exporting

Slips active response includes logging alerts and evidence, optionally exporting them to external systems, and optionally triggering a defense module.

Alerts and evidence are persisted and exposed through the commandline and web frontends, with the native alerts.json log written in IDMEFv2 [25] as described above.

The exporting alerts module can send notifications to Slack, send evidence to a TAXII [23] server, or exchange IDEA events through CESNET Warden [9].

When prevention is enabled, Slips uses its defense modules to block trafic to and from an attacker through the host’s iptables firewall [45]. On a local network, Slips can instead use ARP poisoning as a defense mechanism to block all trafic to and from the detected attacker. This happens in two steps: (1) isolating the attacker from the gateway, which makes the attacker unable to access the internet, and (2) disrupting other local hosts’ connections to and from the attacker, which makes the attacker unreachable.

Both defense mechanisms include automatic unblocking. After being blocked, a profile enters a probation period defined in time windows. New alerts extend this period, while a profile that generates no additional evidence is automatically unblocked when the probation period ends.

## 3 Evaluation Methodology

The goal of the evaluation is to show that the current Slips archi tecture can produce good detections similar to SOTA IDS. The eval uation contains two sets of packet captures with diferent purposes. The first set contains three controlled vertical port-scan captures and evaluates whether the architecture represents the behavior distributed across flows as accountable evidence. The second set contains malware and benign captures and compares the detection decisions of Slips and Suricata. Table 1 summarizes the six captures used in the two experiment sets.

Suricata is used here because it is a widely deployed, mature, feature-rich IDS that represents a strong production baseline rather than a one-of research method.

These datasets are intentionally illustrative. They are not meant to represent the full detection coverage of either Slips or Suricata. Both systems can detect many behaviors that are not present in these captures, so the evaluation should be read as an architec tural demonstration with a small controlled comparison, not as a benchmark of general IDS capability.

## 3.1 Ground Truth and Expert Labeling

Domain experts establish the ground truth before running either detection system. They inspect the capture context, identify the malicious hosts, attack intervals, and relevant trafic, and encode those judgments as labeling conditions.

We then apply the open-source NetFlowLabeler tool [3] which applies the expert-authored conditions to individual flows and produces generic and detailed labels. The tool makes the labeling procedure repeatable; it does not replace the expert judgment used to define the conditions.

For binary evaluation, flows labeled as malicious form the posi tive class. Flows labeled as benign or background form the negative class. The artifacts accompanying this paper [5] include the PCAP files (IDSEVAL dataset), labeling configurations, and the cryptographic hashes.

## 3.2 Experiment Set 1: Port-Scans

The first experiment uses three PCAPs containing known port scans (done using the nmap tool) and evaluates both Slips and Suricata to understand whether each detects them and how each tool reports them. For Slips, each capture was processed with Slips v1.1.21, a one-hour time window, an evidence threshold of 15, and the default module configuration. We then report, for each capture, whether Slips generates any evidence of vertical or horizontal scans. We record whether evidence was generated, the accumulated evidence score, and whether the evidence triggered an alert.

For Suricata, each capture was processed by Suricata v8.0.4 (RE-LEASE) with the Emerging Threats Open ruleset $8 . 0 . 4 ^ { 2 }$ and the default configuration. We then report, for each capture, whether Suricata produced a corresponding scan alert.

In this experiment, the comparison is descriptive because the systems expose diferent intermediate objects: Slips generates evidence and alerts, whereas Suricata generates rule alerts.

Portscans-1 to Portscans-3 contain only port-scanning trafic, so they cannot be used to measure overall accuracy but only recall. In particular, we cannot tell how often the systems would raise scan alerts on benign trafic because this dataset does not include a defined set of “non-scan” examples. Also, the labelling was done flow by flow, but the concept of what is a port scan is left to the IDSs.

Instead, this experiment checks how Slips behaves in comparison with Suricata by asking whether it can (1) recognize scanning patterns that span many connections, and (2) keep a clear trail showing which connections led to that conclusion.

## 3.3 Experiment Set 2: Malware and Benign Trafic

The second experiment evaluates detection performance using two complementary trafic groups: malicious malware captures and benign user trafic. The malicious group consists of Malware-1 and Malware-2, while the benign group consists of Benign-1. Malware-1 contains Bladabindi RAT trafic and Malware-2 contains TrickBot trafic [13, 27]. Both Slips and Suricata process the same captures.

Slips first converts each PCAP into Zeek flows and then makes decisions per host profile and time window. Suricata processes the original PCAPs directly and reports rule-based alerts.

We compare Slips and Suricata from two perspectives: the flow level and the profile-time-window level. At the flow level, a Slips prediction is considered malicious when the flow identifier is linked to evidence. A Suricata prediction is considered malicious when one of its alerts can be mapped to that flow. The flow-by-flow level was chosen because it is how Suricata works by default.

For the benign capture, Benign-1, any detected flow is counted as a false positive because the PCAP contains benign social media browsing trafic and no malicious activity. All remaining undetected benign flows are counted as true negatives.

In addition to the flow-level comparison, we also evaluate both tools at the profile-time-window level because this corresponds to the native decision unit used by Slips. In the ground truth, a profile-time-window is considered malicious if it contains at least one malicious flow in that profile-time-window.

Slips directly provides predictions at this level, whereas for Suricata, alerts are post-processed and grouped by IP address and assigned to the same time-window boundaries used by Slips.

This profile-time-window-level comparison evaluates whether each system can identify malicious host behavior as it develops over time, rather than only detecting individual malicious flows in isolation.

Table 1: Evaluation datasets used to assess evidence generation for vertical port scans and to compare Slips and Suricata on malware and benign user trafic.

<table><tr><td>Experiment set ID</td><td>PCAP ID</td><td>Capture</td><td>Traffic content</td><td>Evaluation purpose</td></tr><tr><td>1</td><td>Portscans-1</td><td>idseval-malicious-portscan-1.pcap</td><td>Vertical port scan (100 ports)</td><td>Evidence generation</td></tr><tr><td>1</td><td>Portscans-2</td><td>idseval-malicious-portscan-2.pcap</td><td>Vertical port scan (1,000 ports)</td><td>Evidence generation</td></tr><tr><td>1</td><td>Portscans-3</td><td>idseval-malicious-portscan-3.pcap</td><td>Vertical port scan (65,536 ports)</td><td>Evidence generation</td></tr><tr><td>2</td><td>Malware-1</td><td>idseval-malicious-malware-1.pcap</td><td>Bladabindi RAT</td><td>Performance comparison</td></tr><tr><td>2</td><td>Malware-2</td><td>idseval-malicious-malware-2.pcap</td><td>TrickBot malware</td><td>Performance comparison</td></tr><tr><td>2</td><td>Benign-1</td><td>idseval-benign-user-traffic-1.pcap</td><td>Social media browsing</td><td>Performance comparison</td></tr></table>

## 3.4 Metrics and Statistical Reporting

For Malware-1 and Malware-2 datasets, the primary quantities are true positives and false negatives, from which we compute recall as $T P / ( T P + F N )$ . For Benign-1, we report false positives and true negatives and compute the false-positive rate as $F P / ( F P + T N )$ Across the combined malware and benign sets, we additionally report precision, specificity, F1 score, and the complete confusion matrix for both systems.

Metrics are reported separately for the flow-level and profile time-window evaluation views. Per-capture results are provided in the accompanying artifacts, while the results section reports aggregate metrics computed using micro-aggregation.

## 3.5 Systems, Controls, and Reproducibility

For every run, we record the Slips and Suricata versions, enabled Slips modules, Suricata ruleset, configuration files, time window width, evidence threshold, analysis direction, command lines, and execution environment.

Slips and Suricata receive identical PCAPs.

Detection outputs for each system are generated before the com parison tool reads them, and ground-truth labels are not available to either system during detection.

The reproducible pipeline has four stages. First, Zeek converts each PCAP into zeek logs. Second, NetFlowLabeler applies the expert-authored labeling configuration to produce the flow-level ground truth. Third, Slips and Suricata process the capture independently. Fourth, the IDPS comparison tool[2] maps evidence and alerts with the labeled flows, constructs the profile-time-window view, and computes the selected metrics.

The artifact accompanying this paper [5] contains all mentioned PCAPs, checksums, labeling configurations, the expected output of each tool used, and the steps used to conduct the two experiment sets.

## 4 Results and Discussion

## 4.1 Experiment Set 1: Port-Scan Evidence Generation Results

For Portscans-1, Slips generated two scan evidence items and raised no alerts because the accumulated evidence did not reach the con figured alert threshold. For Portscans-2, Slips generated one scan evidence item and also raised no alerts. Finally, for Portscans-3, Slips generated five evidence items, but raised no alerts.

For Slips, this is the expected behavior when dealing with portscans: Slips recognizes the port-scan behavior and stores evidence items, but it does not treat one isolated scan as suficient for a host-level

alert. In the current configuration, Slips needs more evidence before deciding to act against that IP address. However, the port scans are detected correctly for the analyst.

In contrast, Suricata raised zero alerts across Portscans-1–Portscans-3. This is surprising, since a port scan should at least acknowledge the security analysts.

The results are shown in Table 2. The table presents the evidence generation, accumulated score, alert thresholding, and alert generation instead of a confusion matrix because our goal here is not to compare the accuracy of the two systems, but to demonstrate how each tool deals with attacks that happen over time.

The important distinction in this experiment is therefore not only whether an alert is raised, but whether the system exposes an intermediate representation showing that the scan was understood. In Slips’ case, the intermediate representation is evidence. In Suricata’s case, there is none.

The evidence generated by Slips and their links to supporting flows are available in the alerts.json file included in the Slips output artifacts.

## 4.2 Experiment Set 2: Malware and Benign Trafic Results

As shown in Table 3, at the flow level, Slips produced 3,610 true positives and 37,834 false negatives, resulting in a recall of 8.71e-2. It also produced 2 false positives and 78,740 true negatives, yielding a precision of 9.994e-1, an FPR of 2.5e-5, and an F1 score of 1.603e-1. Suricata produced 68 true positives and 41,376 false negatives, resulting in a substantially lower recall of 1.6e-3 and an F1 score of 3.3e-3. It produced the same 2 false positives and 78,740 true negatives, with a precision of 9.714e-1 and an FPR of 2.5e-5. Thus, Slips achieved substantially higher malicious-flow coverage without increasing the number of false positives.

At the profile-time-window level, Slips produced 33 true positives and 136 false negatives, achieving a recall of 1.953e-1 and an F1 score of 3.268e-1. Suricata produced 18 true positives and 151 false negatives, yielding a recall of 1.065e-1 and an F1 score of 1.925e-1. Both systems produced 0 false positives and 1,495 true negatives, resulting in a precision of 1 and an FPR of 0.

Overall, Slips performed better than Suricata at both evaluation levels because it achieved higher recall and F1 scores while maintaining the same negligible or zero false-positive rate. Its advantage was especially pronounced at the flow level, where it produced far more true positives than Suricata. At the profile-time-window level, Slips detected 33 malicious profile-time-window pairs, compared with 18 detected by Suricata. This indicates that Slips was more efective at identifying malicious behavior over time, which is consistent with the profile-time-window being its primary decision unit.

Table 2: Port-scan evidence and alert-threshold behavior on the IDSEVAL scan captures. The table reports whether scan-related evidence was generated, the accumulated score for the scanner profile during the experiment time window, the configured alert threshold, and the resulting alert decision.

<table><tr><td>ID</td><td>IDS</td><td>Evidence Generated</td><td>Accumulated Score</td><td>Alert Threshold Per Hour</td><td>Alerts Generated</td></tr><tr><td>Portscans-1</td><td>Slips</td><td>Yes</td><td>2.85</td><td>15</td><td>No</td></tr><tr><td>Portscans-1</td><td>Suricata</td><td>No</td><td>-</td><td>N/A</td><td>No</td></tr><tr><td>Portscans-2</td><td>Slips</td><td>Yes</td><td>1.3</td><td>15</td><td>No</td></tr><tr><td>Portscans-2</td><td>Suricata</td><td>No</td><td>-</td><td>N/A</td><td>No</td></tr><tr><td>Portscans-3</td><td>Slips</td><td>Yes</td><td>7.99</td><td>15</td><td>No</td></tr><tr><td>Portscans-3</td><td>Suricata</td><td>No</td><td>-</td><td>N/A</td><td>No</td></tr></table>

However, the recall of both systems remained low, meaning that neither provided comprehensive coverage of the malicious activity. The improvement observed for both systems at the profile-timewindow level compared with their flow-by-flow results indicates that their detections are more efective for recognizing malicious host behavior accumulated across time than for labeling every individual malicious flow.

## 5 Decision Case Study

Alerts show whether Slips detected a malicious profile, but they do not show how the decision was made. We therefore trace one Slips alert from Malware-1, the Bladabindi RAT malware capture. The trace shows the complete path from a host-level alert to correlated evidence and then to the flow identifiers stored in the SQLite database.

The selected alert is reported for host 192.168.1.115 in time window 2. The run used Slips with a one-hour time window, analysis direction out, and an evidence threshold of 15 per hour. Slips created incident 749e232c-acee-4817-82f7-d71675ed1967 when the accumulated threat level for this profile and time window reached 15.0.

The incident contains a CorrelID list with 60 evidence identifiers. These correspond to 30 medium-severity evidence items and 30 informational evidence items.

The medium evidence items report repeated connections from 192.168.1.115 to the unknown destination port 1177/TCP on 41.108.179.197. Each medium item has confidence 1.0 and con tributes 0.5 to the accumulated score.

The informational items indicate that the same destination IP was contacted without DNS resolution; they are retained for context but do not increase the score.

The evidence-to-flow link is explicit. For example, the evidence item 608dadb5-46a7-46f1-b348-4d9ea1379370, which is one of the 60 evidence items reported by the above alert, points to flow UID CJJC2G1hvW8XwV9cu3.

Another is 7fb57255-3868-4ccf-96de-9ebbab62b548, which points to flow UID CzNzeW1yR9E17jomgg. The latter flow is a TCP connection from 192.168.1.115:60308 to 41.108.179.197:1177, with Zeek state S0, duration 9.009 s, three source packets, and no destination packets.

This chain lets an analyst move from the alert to the evidence and then to the concrete network observations.

This example uses heuristic evidence, but the same path is used by ML modules. An ML module emits evidence with a threat level, confidence, and flow identifiers; the evidence handler then combines it with other evidence for the same profile and time window. The final decision is therefore not an opaque model output. It is an accumulated host-level decision with stored links to the observations that supported it.

## 6 Previous Work: IDS Architectures

We distinguish complete or prototype IDS architectures from classifiers evaluated only on benchmark rows without a defined acquisition, state, alert, or response pipeline. Table 4 compares systems that define an operational pipeline or explicit multi-component architecture. There, a flow means packets aggregated with defined key and time semantics, not merely one dataset row.

Production systems retain substantial multi-packet state. Snort 3 and Suricata combine decoding, stream or flow state, protocol inspection, rules, and actions [36, 40]; Zeek converts packets into events that scripts correlate across connections [38]. They support stateful detections, but do not impose a detector-independent host profile and general evidence-accumulation decision.

Behavioral models also retain context, but usually for one model family. Kitsune maintains address- and channel-keyed statistics over several decay windows [28]; DÏoT models ordered packet sequences per IoT device [30]; and APChain compares chains of trafic attributes with a learned host model [43]. Their context is richer than one packet or flow, but their state and output remain specific to the corresponding detector.

Graph and correlation architectures combine lower-level observations. GrIDS reduces communication graphs, BotDet correlates Zeek-based detectors, and a peer-to-peer CIDS combines reports from several networks [11, 16, 53]. Their intermediate representations are task-specific rather than a general evidence object carrying threat, confidence, and supporting-flow references.

Model ensembles and modular pipelines provide another form of composition [1, 19, 21, 39, 50]. They combine classifiers, agents, or IDS engines, but do not jointly provide shared host state, evidence accumulated over time, and provenance to supporting flows.

Table 3: Trafic detection comparison on Malware-1, Malware-2, and Benign-1. FPR is computed as $F P / ( F P + T N )$ .

<table><tr><td>Type</td><td>System</td><td>TP</td><td>FN</td><td>FP</td><td>TN</td><td>Precision</td><td>Recall</td><td>F1</td><td>FPR</td></tr><tr><td>Flow-by-flow</td><td>Slips</td><td>3610</td><td>37834</td><td>2</td><td>78740</td><td>0.9994</td><td>0.0871</td><td>0.1603</td><td>0.000025</td></tr><tr><td>Flow-by-flow</td><td>Suricata</td><td>68</td><td>41376</td><td>2</td><td>78740</td><td>0.9714</td><td>0.0016</td><td>0.0033</td><td>0.000025</td></tr><tr><td>Profile-window</td><td>Slips</td><td>33</td><td>136</td><td>0</td><td>1495</td><td>1.0000</td><td>0.1953</td><td>0.3268</td><td>0.000000</td></tr><tr><td>Profile-window</td><td>Suricata</td><td>18</td><td>151</td><td>0</td><td>1495</td><td>1.0000</td><td>0.1065</td><td>0.1925</td><td>0.000000</td></tr></table>

## 7 Discussion and Limitations

The architecture relies on shared state and calibrated evidence scores. IP-based profiles can merge devices behind address transla tion or split one device after an address change, while time-window boundaries can divide behavior. Correlated modules may detect overlapping aspects of the same behavior, causing related evidence to be counted multiple times and potentially inflating the result ing confidence and accumulated threat level score. The illustrative evaluation does not assess the impact of these architectural limi tations, Slips’ ability to analyze encrypted trafic, its resistance to adversarial evasion, its privacy implications, or its performance at operational scale.

## 8 Conclusion

Slips combines time-bounded host profiles, independent detection modules, and evidence-based decisions in one network security architecture. The design lets AI and non-AI modules contribute traceable findings without directly controlling the final alert. The evaluation illustrates this separation and its provenance, but sup ports conclusions only for the tested captures and configurations.

## References

[1] Sarah Alharbi and Arshiya Khan. 2024. Ensemble Defense System: A Hybrid IDS Approach for Efective Cyber Threat Detection. In 2023 33rd International Telecommunication Networks and Applications Conference. doi:10.1109/ITNAC5 9571.2023.10368510

[2] Anonymous Authors. 2026. IDPS Comparison Tool. https://anonymous.4open. science/r/IDPS-Comparison-Tool-B1F0/

[3] Anonymous authors. 2026. NetFlowLabeler: A Configurable Rule-Based Labeling Tool for Network Flow Files. Anonymized software artifact. https://anonymous. 4open.science/r/netflowlabeler-60E1/

[4] Anonymous authors. 2026. Slips: Behavioral Machine Learning-Based Intrusion Prevention System. Anonymized software artifact. https://anonymous.4open.sc ience/r/Slips-731B

[5] Anonymous User. 2026. Anonymized Slips Paper Artifacts. Artifact repository containing PCAP files, labeling configurations, cryptographic hashes, experiment inputs, tool outputs, result-generation files, and reproduction instructions. doi:10 .5281/zenodo.21344815

[6] Anonymous Author. [n. d.]. Modelling The Network Behavior of Malware to Block Malicious Patterns. A Behavioral IPS. AnonymizedLink

[7] Anonymous Authors. 2026. Security Datasets for Testing: a set of security datasets for testing of tools and algorithms. https://anonymous.4open.science/status/sec urity-datasets-for-testing-B3B9

[8] Stefan Axelsson. 2000. Intrusion Detection Systems: A Survey and Taxonomy. Technical report, Department of Computer Engineering, Chalmers University of Technology. https://www.cse.msu.edu/\~cse960/Papers/security/axelsson00intr usion.pdf

[9] CESNET. 2017. Warden. CESNET, z. s. p. o. https://warden.cesnet.cz/en/index

[10] CESNET. 2026. Intrusion Detection Extensible Alert (IDEA). CESNET, z. s. p. o. https://idea.cesnet.cz/en/index

[11] Steven Cheung, Rick Crawford, Mark Dilger, Jeremy Frank, Jim Hoagland, Karl Levitt, Jef Rowe, Stuart Staniford-Chen, Raymond Yip, and Dan Zerkle. 1999. The Design of GrIDS: A Graph-Based Intrusion Detection System. Technical Report SCE-99-2. University of California, Davis, Department of Computer Science. https://seclab.cs.ucdavis.edu/projects/arpa/grids/grids.pdf

[12] Kyunghyun Cho, Bart van Merriënboer, Caglar Gülçehre, Dzmitry Bahdanau, Fethi Bougares, Holger Schwenk, and Yoshua Bengio. 2014. Learning Phrase Representations using RNN Encoder-Decoder for Statistical Machine Translation.

arXiv preprint arXiv:1406.1078 (2014). https://arxiv.org/abs/1406.1078

[13] Cybersecurity and Infrastructure Security Agency. 2021. TrickBot Malware. Advisory AA21-076A. https://www.cisa.gov/news-events/cybersecurityadvisories/aa21-076a

[14] Nicolas Falliere. 2011. Sality: Story ofa Peer-to-Peer Viral Network. Technical Report. Symantec Security Response. Version 1.0. https://aroundcyber.wordpr ess.com/wp-content/uploads/2012/11/sality\_peer\_to\_peer\_viral\_network.pdf

[15] Foofus.net. 2026. Medusa Parallel Network Login Auditor. Project repository. https://github.com/jmk-foofus/medusa

[16] Ibrahim Ghafir, Vaclav Prenosil, Mohammad Hammoudeh, Thar Baker, Sohail Jabbar, Shehzad Khalid, and Sardar Jaf. 2018. BotDet: A System for Real Time Botnet Command and Control Trafic Detection. IEEE Access (2018). doi:10.1109/ ACCESS.2018.2846740

[17] Guofei Gu, Phillip Porras, Vinod Yegneswaran, Martin Fong, and Wenke Lee. 2007. BotHunter: Detecting Malware Infection through IDS-Driven Dialog Correlation. In Proceedings ofthe 16th USENIX Security Symposium. USENIX Association, 167–182. doi:10.5555/1362903.1362915

[18] Peter Haag and the nfdump contributors. 2026. nfdump: NetFlow Processing Tools. Software repository and documentation. Accessed 2026-07-15. https: //github.com/phaag/nfdump

[19] Mehrdad Hajizadeh, Sudip Barua, and Pegah Golchin. 2023. FSA-IDS: A Flow-Based Self-Active Intrusion Detection System. In NOMS 2023-2023 IEEE/IFIP Network Operations and Management Symposium. IEEE. doi:10.1109/NOMS5692 8.2023.10154343

[20] Guy Harris and Michael Richardson. 2026. PCAP Capture File Format. Internet-Draft draft-ietf-opsawg-pcap-08. Work in progress; accessed 2026-07-21. https: //datatracker.ietf.org/doc/draft-ietf-opsawg-pcap

[21] Álvaro Herrero, Martí Navarro, Emilio Corchado, and Vicente Julián. 2013. RT-MOVICAB-IDS: Addressing Real-Time Intrusion Detection. Future Generation Computer Systems (2013). doi:10.1016/j.future.2010.12.017

[22] Bret Jordan, Rich Piazza, and Trey Darley (Eds.). 2021. STIX Version 2.1. OASIS Open. OASIS Standard. https://docs.oasis-open.org/cti/stix/v2.1/os/stix-v2.1- os.html

[23] Bret Jordan and Drew Varner (Eds.). 2021. TAXII Version 2.1. OASIS Open. OASIS Standard. https://docs.oasis-open.org/cti/taxii/v2.1/os/taxii-v2.1-os.html

[24] Victor Le Pochat, Tom Van Goethem, Samaneh Tajalizadehkhoob, Maciej Korczyński, and Wouter Joosen. 2019. Tranco: A Research-Oriented Top Sites Ranking Hardened Against Manipulation. In Proceedings ofthe Network and Distributed System Security Symposium (NDSS). Internet Society, San Diego, CA, USA, 15 pages. Accompanying online service: https://tranco-list.eu/. doi:10.14722/ndss.2019.23386

[25] Gilles Lehmann. 2026. The Incident Detection Message Exchange Format version 2 (IDMEFv2). Internet-Draft draft-lehmann-idmefv2-08, IETF. Published 2026- 04-26; intended status: Standards Track; maintained by the IDMEFv2 Task Force. https://datatracker.ietf.org/doc/html/draft-lehmann-idmefv2-08

[26] libssh Project. 2026. libssh – The SSH Library! https://www.libssh.org/

[27] Microsoft. 2013. Backdoor:MSIL/Bladabindi. https://www.microsoft.com/en-us /wdsi/threats/malware-encyclopedia-description?name=MSIL%2FBladabindi

[28] Yisroel Mirsky, Tomer Doitshman, Yuval Elovici, and Asaf Shabtai. 2018. Kitsune: An Ensemble of Autoencoders for Online Network Intrusion Detection. In Proceedings 2018 Network and Distributed System Security Symposium. Internet Society, Reston, VA, USA. doi:10.14722/ndss.2018.23204

[29] MITRE ATT&CK. 2020. Internet Connection Discovery, Sub-technique T1016.001. https://attack.mitre.org/techniques/T1016/001/

[30] Thien Duc Nguyen, Samuel Marchal, Markus Miettinen, Hossein Fereidooni, N. Asokan, and Ahmad-Reza Sadeghi. 2019. DÏoT: A Federated Self-learning Anomaly Detection System for IoT. In 2019 IEEE 39th International Conference on Distributed Computing Systems (ICDCS). IEEE. doi:10.1109/ICDCS.2019.00080

[31] Peng Ning, Yun Cui, and Douglas S. Reeves. 2002. Constructing attack scenarios through correlation of intrusion alerts. In Proceedings ofthe 9th ACM Conference on Computer and Communications Security (Washington, DC, USA) (CCS ’02). Association for Computing Machinery, New York, NY, USA, 245–254. doi:10.114 5/586110.586144

[32] NIST Computer Security Resource Center. 2025. SOAR. NIST Glossary. Glossary entry citing NIST IR 8401, NIST SP 800-18r2, NIST SP 800-215, and NIST SP 800-61r3. https://csrc.nist.gov/glossary/term/soar

[33] Nmap Project. 2026. Ncrack Reference Guide. https://nmap.org/ncrack/man.html

[34] Open Information Security Foundation. [n. d.]. Thresholding Keywords. Suricata User Guide. https://docs.suricata.io/en/latest/rules/thresholding.html

[35] Open Information Security Foundation. 2026. EVE JSON Output. Suricata User Guide. Accessed 2026-07-15. https://docs.suricata.io/en/latest/output/eve/evejson-output.html

[36] Open Information Security Foundation. 2026. OISF/suricata: Suricata source repository. https://github.com/OISF/suricata.

[37] Paramiko Project. 2026. Welcome to Paramiko. https://www.paramiko.org/

[38] Vern Paxson. 1999. Bro: A System for Detecting Network Intruders in Real-Time. Computer Networks 31, 23–24 (1999), 2435–2463. doi:10.1016/S1389- 1286(99)00112-7

[39] Yan Qiao and Weixin Xie. 2002. A Network IDS with Low False Positive Rate. In Proceedings ofthe 2002 Congress on Evolutionary Computation. CEC’02. IEEE. doi:10.1109/CEC.2002.1004400

[40] Martin Roesch. 1999. Snort: Lightweight Intrusion Detection for Networks. In Proceedings ofthe 13th USENIX Conference on System Administration (LISA ’99). USENIX Association, 229–238. https://www.usenix.org/event/lisa99/full\_paper s/roesch/roesch\_html/

[41] Salesforce Engineering. 2018. TLS Fingerprinting with JA3 and JA3S. https://en gineering.salesforce.com/tls-fingerprinting-with-ja3-and-ja3s-247362855967/

[42] Mike Schuster and Kuldip K. Paliwal. 1997. Bidirectional Recurrent Neural Networks. IEEE Transactions on Signal Processing 45, 11 (1997), 2673–2681. doi:10 .1109/78.650093

[43] Jungwoo Seo and Sangjin Lee. 2018. Abnormal Behavior Detection to Identify Infected Systems Using the APChain Algorithm and Behavioral Profiling. Security and Communication Networks (2018). doi:10.1155/2018/9706706

[44] The Argus Project. 2026. Argus Network Flow Monitoring System. Argus Project Documentation. Accessed 2026-07-15. https://openargus.org/

[45] The Netfilter Project. 2026. The netfilter.org “iptables” Project. Accessed: 2026- 07-16. https://www.netfilter.org/projects/iptables/index.htm

[46] The Zeek Project. 2026. Log Files. Book of Zeek Documentation. Accessed 2026-07-15. https://docs.zeek.org/en/lts/script-reference/log-files.html

[47] Michael Tüxen, Fulvio Risso, Jasper Bongertz, Gerald Combs, Guy Harris, Eelco Chaudron, and Michael Richardson. 2026. PCAP Now Generic (pcapng) Capture File Format. Internet-Draft draft-ietf-opsawg-pcapng-05. Work in progress; accessed 2026-07-21. https://datatracker.ietf.org/doc/draft-ietf -opsawg-pcapng/

[48] Fredrik Valeur, Giovanni Vigna, Christopher Kruegel, and Richard A. Kemmerer. 2004. A Comprehensive Approach to Intrusion Detection Alert Correlation. IEEE Transactions on Dependable and Secure Computing 1, 3 (2004), 146–169. doi:10.1109/TDSC.2004.21

[49] van Hauser/THC and David Maciejak. 2026. THC-Hydra. Project repository. https://github.com/vanhauser-thc/thc-hydra

[50] Miel Verkerken, Laurens D’hooge, Didik Sudyana, Ying-Dar Lin, Tim Wauters, Bruno Volckaert, and Filip De Turck. 2023. A Novel Multi-Stage Approach for Hierarchical Intrusion Detection. IEEE Transactions on Network and Service Management (2023). doi:10.1109/TNSM.2023.3259474

[51] VirusTotal. 2026. YARA. Oficial documentation. https://virustotal.github.io/yar a/

[52] Wireshark Foundation. 2026. tshark(1) Manual Page. NAME: tshark - Dump and analyze network trafic. https://www.wireshark.org/docs/man-pages/tshark.h tml

[53] Chenfeng Vincent Zhou and Shanika Karunasekera. 2005. A Peer-to-Peer Col laborative Intrusion Detection System. In 2005 13th IEEE International Conference on Networks Jointly held with the 2005 IEEE 7th Malaysia International Conference on Communication, Vol. 1. IEEE, Piscataway, NJ, USA. doi:10.1109/ICON.2005.16 35451

## 9 Ethical Considerations

All network captures used in this paper were produced by the au thors in a controlled laboratory environment under their exclusive control. The benign capture records the authors’ own browsing ac tivity; the malicious captures were produced by executing malware samples and launching port scans on an isolated network segment.

## 10 Generative AI Usage

Generative AI tools were used to assist with software develop ment/debugging and with manuscript structural flow and grammar. The authors are responsible for the research, validation, and final manuscript.

## A Detailed IDS Architecture Comparison

Table 4 compares the architectures of selected prior intrusion detection systems.

## B Open Science Appendix

All datasets, tools, experimental results, and supporting artifacts used in this paper have been anonymized and made publicly available to support reproducibility. Because the complete artifact package exceeds GitHub’s recommended repository and file size limits, it has been compressed and hosted in an anonymized Zenodo repository:

https://zenodo.org/records/21344815

Table 4: Architectural comparison of prior intrusion detection systems, ordered by creation year. “Created” refers to the system’s first implementation or introduction rather than the publication year of the cited source.

<table><tr><td>System</td><td>Created</td><td>Input unit</td><td>Multi-packet or multi-flow context</td><td>Profile</td><td>Decision hierarchy</td><td>Ensemble/fusion</td></tr><tr><td>Zeek (Bro) [38]</td><td>1995</td><td>Packets converted to typed protocol events</td><td>Stateful connections, transactions, and scripts over event streams</td><td>Script-defined host state</td><td>Packet → protocol event → script notice/action</td><td>Scripted correlation; no default weighted ensemble</td></tr><tr><td>GrIDS [11]</td><td>1996</td><td>Network activity reports</td><td>Communication graphs, reductions, and administrative hierarchy</td><td>Hosts as attributed graph entities</td><td>Report → graph → rule match → alert</td><td>Rule/report aggregation</td></tr><tr><td>Snort [40]</td><td>1998</td><td>Packets and reconstructed streams</td><td>Flow tracking, TCP reassembly, service inspection, and rule-local thresholds</td><td>No shared behavioral host profile</td><td>DAQ packet → codec/inspector → rule → action/output</td><td>No general alert fusion</td></tr><tr><td>AINIDS [39]</td><td>2002</td><td>Packet headers</td><td>Detector matches plus monitor-agent state</td><td>Resource and detector state; not a host profile</td><td>Match → co-stimulation → intrusion</td><td>Heterogeneous danger signals</td></tr><tr><td>P2P CIDS [53]</td><td>2005</td><td>Suspicious-source reports</td><td>Corroboration across subnetworks</td><td>Minimal source-IP record</td><td>Local report → distributed correlation → alert</td><td>Multi-sensor agreement</td></tr><tr><td>Suricata [36]</td><td>2007</td><td>Packets, flows, streams, and application transactions</td><td>Bidirectional flow state, reassembly, application parsers, and rule-local thresholds</td><td>No shared behavioral host profile</td><td>Capture/decode → flow/stream/application layer → signature → alert/drop</td><td>No general alert fusion</td></tr><tr><td>RT-MOVICAB-IDS [21]</td><td>2013</td><td>TCP packet features</td><td>Incremental learned cases; no explicit multi-flow host window</td><td>No</td><td>Projection → neural analysis → case-based decision/action</td><td>Hybrid ANN and case-based reasoning</td></tr><tr><td>APChain [43]</td><td>2018</td><td>Network-traffic attributes</td><td>Chains of related host communications over time</td><td>Per-host learned behavior model</td><td>Traffic → chain → deviation → infected host</td><td>No</td></tr><tr><td>BotDet [16]</td><td>2018</td><td>Zeek connection and DNS events</td><td>Per-host counters, DNS behavior, and event correlation</td><td>Module-specific host tables</td><td>Event → module detection → correlated bot alert</td><td>Four heterogeneous detectors</td></tr><tr><td>Kitsune [28]</td><td>2018</td><td>Packets</td><td>Damped address and channel statistics at multiple time scales</td><td>Implicit address and address-pair statistics</td><td>Packet → features → reconstruction errors → anomaly score</td><td>Autoencoder ensemble</td></tr><tr><td>DIoT [30]</td><td>2019</td><td>Packets encoded as symbols</td><td>Ordered packet sequences</td><td>Device type and learned communication model</td><td>Packet → sequence score → device alert</td><td>Federated model aggregation</td></tr><tr><td>FSA-IDS [19]</td><td>2023</td><td>Argus five-tuple flows</td><td>Packets only within each flow</td><td>No</td><td>Flow → ensemble uncertainty → pseudo-label/expert query</td><td>Supervised classifier ensemble</td></tr><tr><td>Hierarchical IDS [50]</td><td>2023</td><td>Benchmark flow records</td><td>No context across flows</td><td>No</td><td>Benign/suspicious → class/unknown</td><td>No; serial classifiers</td></tr><tr><td>EDS [1]</td><td>2023</td><td>Traffic plus outputs from three IDS engines</td><td>Delegated to constituent IDSs</td><td>Searchable events; no unified profile</td><td>Detector output → SIEM index/dashboard</td><td>Parallel IDS aggregation</td></tr></table>