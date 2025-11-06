--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5 (Debian 17.5-1)
-- Dumped by pg_dump version 17.5 (Debian 17.5-1)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: public; Type: SCHEMA; Schema: -; Owner: klax
--

-- *not* creating schema, since initdb creates it


ALTER SCHEMA public OWNER TO klax;

--
-- Name: SCHEMA public; Type: COMMENT; Schema: -; Owner: klax
--

COMMENT ON SCHEMA public IS '';


--
-- Name: authmethod; Type: TYPE; Schema: public; Owner: cage
--

CREATE TYPE public.authmethod AS ENUM (
    'password',
    'oauth',
    'sso'
);


ALTER TYPE public.authmethod OWNER TO cage;

--
-- Name: entitytype; Type: TYPE; Schema: public; Owner: cage
--

CREATE TYPE public.entitytype AS ENUM (
    'ministry',
    'department',
    'agency',
    'county_assembly',
    'commission',
    'SAGA',
    'state_corporation'
);


ALTER TYPE public.entitytype OWNER TO cage;

--
-- Name: govlevel; Type: TYPE; Schema: public; Owner: cage
--

CREATE TYPE public.govlevel AS ENUM (
    'county',
    'national'
);


ALTER TYPE public.govlevel OWNER TO cage;

--
-- Name: policyeffect; Type: TYPE; Schema: public; Owner: cage
--

CREATE TYPE public.policyeffect AS ENUM (
    'ALLOW',
    'DENY'
);


ALTER TYPE public.policyeffect OWNER TO cage;

--
-- Name: userstatus; Type: TYPE; Schema: public; Owner: cage
--

CREATE TYPE public.userstatus AS ENUM (
    'active',
    'inactive',
    'deleted',
    'suspended'
);


ALTER TYPE public.userstatus OWNER TO cage;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: abac_policies; Type: TABLE; Schema: public; Owner: cage
--

CREATE TABLE public.abac_policies (
    id integer NOT NULL,
    description text NOT NULL,
    effect public.policyeffect NOT NULL,
    user_attributes json NOT NULL,
    action_names json NOT NULL,
    resource_attributes json NOT NULL,
    priority integer NOT NULL,
    is_active boolean NOT NULL
);


ALTER TABLE public.abac_policies OWNER TO cage;

--
-- Name: abac_policies_id_seq; Type: SEQUENCE; Schema: public; Owner: cage
--

CREATE SEQUENCE public.abac_policies_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.abac_policies_id_seq OWNER TO cage;

--
-- Name: abac_policies_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: cage
--

ALTER SEQUENCE public.abac_policies_id_seq OWNED BY public.abac_policies.id;


--
-- Name: activity_logs; Type: TABLE; Schema: public; Owner: cage
--

CREATE TABLE public.activity_logs (
    id uuid NOT NULL,
    user_id character varying(50),
    action character varying,
    target_table character varying,
    target_id character varying,
    logg_level character varying,
    details json,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.activity_logs OWNER TO cage;

--
-- Name: departments; Type: TABLE; Schema: public; Owner: cage
--

CREATE TABLE public.departments (
    dept_id character varying(60) NOT NULL,
    name character varying(100) NOT NULL,
    parent_dept_id character varying(60),
    entity_type public.entitytype NOT NULL,
    description text
);


ALTER TABLE public.departments OWNER TO cage;

--
-- Name: roles; Type: TABLE; Schema: public; Owner: cage
--

CREATE TABLE public.roles (
    id character varying(60) NOT NULL,
    name character varying(50) NOT NULL,
    description character varying(255),
    permissions json,
    created_at timestamp with time zone DEFAULT now()
);


ALTER TABLE public.roles OWNER TO cage;

--
-- Name: users; Type: TABLE; Schema: public; Owner: cage
--

CREATE TABLE public.users (
    id character varying(60) NOT NULL,
    profile_pic character varying(200),
    first_name character varying(100) NOT NULL,
    last_name character varying(100) NOT NULL,
    email character varying(120) NOT NULL,
    phone_number character varying(20),
    department_id character varying(60) NOT NULL,
    position_title character varying(255) NOT NULL,
    is_accounting_officer boolean NOT NULL,
    password_hash character varying NOT NULL,
    role_id character varying(50),
    status public.userstatus NOT NULL,
    created_at timestamp with time zone DEFAULT now(),
    last_login timestamp with time zone,
    gov_level public.govlevel NOT NULL,
    entity_type public.entitytype NOT NULL,
    entity_name character varying(80) NOT NULL,
    location_code character varying(30),
    access_scope json,
    is_two_factor_enabled boolean,
    last_password_change timestamp with time zone,
    login_attempts integer DEFAULT 0 NOT NULL,
    last_activity_at timestamp with time zone,
    notes text,
    auth_method public.authmethod DEFAULT 'password'::public.authmethod NOT NULL
);


ALTER TABLE public.users OWNER TO cage;

--
-- Name: usertokens; Type: TABLE; Schema: public; Owner: cage
--

CREATE TABLE public.usertokens (
    jti character varying(40) NOT NULL,
    iat timestamp with time zone NOT NULL,
    user_id character varying(60),
    exp timestamp with time zone NOT NULL,
    token character varying(500) NOT NULL,
    revoked boolean
);


ALTER TABLE public.usertokens OWNER TO cage;

--
-- Name: abac_policies id; Type: DEFAULT; Schema: public; Owner: cage
--

ALTER TABLE ONLY public.abac_policies ALTER COLUMN id SET DEFAULT nextval('public.abac_policies_id_seq'::regclass);


--
-- Data for Name: abac_policies; Type: TABLE DATA; Schema: public; Owner: cage
--

COPY public.abac_policies (id, description, effect, user_attributes, action_names, resource_attributes, priority, is_active) FROM stdin;
1	Only Accounting Officers can approve high-value disposals	ALLOW	{"is_accounting_officer": true, "gov_level": ["county", "national"]}	["asset.approve_disposal"]	{"disposal_value": {">=": 1000000}, "status": "marked_for_disposal"}	100	t
2	ICT equipment can only be assigned by ICT officers or above	ALLOW	{"position_title": ["ICT Officer", "ICT Manager", "Accounting Officer"], "roles": ["ict_officer", "asset_manager", "accounting_officer"]}	["asset.assign_to_user", "asset.transfer_initiate"]	{"category": "ICT_EQUIPMENT", "status": ["operational", "under_maintenance"]}	90	t
3	Cross-county transfers require National Treasury approval	DENY	{"gov_level": "county"}	["asset.approve_transfer"]	{"transfer_type": "cross_county", "asset_value": {">=": 500000}}	200	t
4	Vehicles can only be transferred by transport officers	ALLOW	{"department_type": ["transport", "administration"], "position_title": ["Transport Officer", "Fleet Manager", "Accounting Officer"]}	["asset.transfer_initiate", "asset.assign_to_user"]	{"category": "MOTOR_VEHICLES", "status": "operational"}	80	t
5	Assets under maintenance cannot be disposed	DENY	{}	["asset.approve_disposal", "asset.mark_disposal"]	{"status": "under_maintenance"}	150	t
\.


--
-- Data for Name: activity_logs; Type: TABLE DATA; Schema: public; Owner: cage
--

COPY public.activity_logs (id, user_id, action, target_table, target_id, logg_level, details, created_at) FROM stdin;
\.


--
-- Data for Name: departments; Type: TABLE DATA; Schema: public; Owner: cage
--

COPY public.departments (dept_id, name, parent_dept_id, entity_type, description) FROM stdin;
ict_default	ICT DEFAULT	\N	ministry	Default department for ICT users
fin_01	Ministry of Finance	\N	ministry	Handles government financial matters
ict_dept	ICT Department	ict_default	department	Oversees ICT operations and infrastructure
audit_agency_01	National Audit Agency	\N	agency	Conducts audits for compliance and accountability
hr_comm_01	Human Resource Commission	\N	commission	Regulates HR policies across the public sector
DEPT_NT_001	National Treasury & Planning	\N	ministry	Handles government financial matters
DEPT_COB_001	Office of the Controller of Budget	\N	agency	Independent office for budget oversight
DEPT_KENHA_001	Kenya National Highways Authority	\N	SAGA	Manages national road infrastructure
DEPT_KIS_FIN	Kisumu County Finance Department	\N	department	County finance and economic planning
DEPT_NAK_ASS	Nakuru County Assembly	\N	county_assembly	Legislative arm of Nakuru County
DEPT_MOB_ICT	Mombasa ICT Department	\N	department	ICT operations for Mombasa County
DEPT_TSC_REG	Teachers Service Commission Regional Offices	\N	commission	Oversees teacher services regionally
DEPT_KPLC_001	Kenya Power and Lighting Company	\N	state_corporation	Manages electricity distribution in Kenya
\.


--
-- Data for Name: roles; Type: TABLE DATA; Schema: public; Owner: cage
--

COPY public.roles (id, name, description, permissions, created_at) FROM stdin;
role_001	asset_manager	Can manage assets within their scope	["asset.create", "asset.read", "asset.update", "asset.transfer_initiate", "asset.maintenance_schedule", "maintenance.create", "maintenance.update"]	2025-08-21 05:03:35.017788-04
role_002	accounting_officer	Senior officer with approval powers	["asset.create", "asset.read", "asset.update", "asset.approve_disposal", "asset.approve_transfer", "asset.write_off", "financial.approve_expenditure", "reports.generate_statutory"]	2025-08-21 05:03:35.017788-04
role_003	auditor	Can view and audit all assets	["asset.read", "asset.audit", "reports.generate_audit", "audit.create_findings", "audit.export_data"]	2025-08-21 05:03:35.017788-04
role_004	ict_officer	Manages ICT assets specifically	["asset.create", "asset.read", "asset.update", "asset.assign_to_user", "maintenance.schedule_ict"]	2025-08-21 05:03:35.017788-04
role_005	system_admin	Full system administrator with all permissions	["*"]	2025-08-21 05:35:07.054829-04
role_006	finance_officer	Manages financial aspects of assets and liabilities	["approve_asset", "view_financials", "reports.generate_financial"]	2025-08-21 05:35:07.054829-04
role_007	super_user	Can override and assign roles	["role.assign", "role.override", "role.view"]	2025-08-21 05:35:07.054829-04
role_008	ministry_user	General ministry staff with limited asset access	["asset.read", "reports.view_summary"]	2025-08-21 05:35:07.054829-04
role_super	super_user_do	A User with all priviledges, testing	["asset.create", "asset.read", "asset.update", "asset.delete","policy.create", "policy.read", "policy.update", "policy.delete","department.create", "department.read", "department.update", "department.delete","users.create","users.read","users.update","users.delete","role.create", "role.read", "role.update", "role.delete"]	2025-08-21 15:30:38.530099-04
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: cage
--

COPY public.users (id, profile_pic, first_name, last_name, email, phone_number, department_id, position_title, is_accounting_officer, password_hash, role_id, status, created_at, last_login, gov_level, entity_type, entity_name, location_code, access_scope, is_two_factor_enabled, last_password_change, login_attempts, last_activity_at, notes, auth_method) FROM stdin;
83cebe3c-0e17-4be0-8084-80b501853c39	http://profile.com/some/pic/here	Jack	doh	user@example.com	+254700678901	ict_default	ICT Officer	f	$2b$12$T6/XA5b1gu5w2Mp53OOUN.poAdDbj4BpU1gLuKPyBJlMnkF2jXkCS	role_super	active	2025-08-21 04:33:30.846811-04	2025-08-21 17:29:02.46908-04	county	department	Mombasa County Government	MOB	"{}"	f	\N	0	\N	somenotes here	password
user_002	\N	Mary	Wanjiku	m.wanjiku@cog.go.ke	+254700234567	DEPT_COB_001	Senior Auditor	f	$2b$12$T6/XA5b1gu5w2Mp53OOUN.poAdDbj4BpU1gLuKPyBJlMnkF2jXkCS	role_003	active	2025-08-21 06:02:08.922297-04	\N	national	agency	Office of the Controller of Budget	\N	{"read_only": true, "audit_access": ["all_counties"], "report_generation": ["financial", "compliance"]}	\N	\N	0	\N	\N	password
user_003	\N	David	Kiprotich	d.kiprotich@kenha.co.ke	+254700345678	DEPT_KENHA_001	Asset Manager	f	$2b$12$T6/XA5b1gu5w2Mp53OOUN.poAdDbj4BpU1gLuKPyBJlMnkF2jXkCS	role_001	active	2025-08-21 06:02:08.922297-04	\N	national	SAGA	Kenya National Highways Authority	\N	{"asset_categories": ["ROAD_INFRASTRUCTURE", "MOTOR_VEHICLES", "PLANT_MACHINERY"], "geographic_scope": ["national_roads"]}	\N	\N	0	\N	\N	password
user_004	\N	Grace	Akinyi	g.akinyi@kisumu.go.ke	+254700456789	DEPT_KIS_FIN	County Executive Committee Member - Finance	t	$2b$12$T6/XA5b1gu5w2Mp53OOUN.poAdDbj4BpU1gLuKPyBJlMnkF2jXkCS	role_008	active	2025-08-21 06:02:08.922297-04	\N	county	department	Kisumu County Government	\N	{"county_code": "KIS", "budget_approval": true, "disposal_approval": true, "asset_approval_limit": 10000000}	\N	\N	0	\N	\N	password
user_005	\N	Peter	Muthoni	p.muthoni@nakuru.assembly.go.ke	+254700567890	DEPT_NAK_ASS	Clerk of County Assembly	t	$2b$12$T6/XA5b1gu5w2Mp53OOUN.poAdDbj4BpU1gLuKPyBJlMnkF2jXkCS	role_008	active	2025-08-21 06:02:08.922297-04	\N	county	county_assembly	Nakuru County Assembly	\N	{"county_code": "NAK", "assembly_assets_only": true, "legislative_equipment": true}	\N	\N	0	\N	\N	password
user_001	\N	John	Kamau	j.kamau@treasury.go.ke	+254700123456	DEPT_NT_001	Principal Accountant	f	$2b$12$T6/XA5b1gu5w2Mp53OOUN.poAdDbj4BpU1gLuKPyBJlMnkF2jXkCS	role_002	active	2025-08-21 05:47:45.347153-04	2025-08-21 06:29:59.593694-04	national	ministry	Ministry of Finance and Planning	\N	{"counties": ["all"], "asset_approval_limit": 50000000, "can_approve_disposals": true}	\N	\N	0	\N	\N	password
user_006	\N	Sarah	Chebet	s.chebet@mombasa.go.ke	+254799678901	DEPT_MOB_ICT	ICT Officer	f	$2b$12$T6/XA5b1gu5w2Mp53OOUN.poAdDbj4BpU1gLuKPyBJlMnkF2jXkCS	role_004	active	2025-08-21 06:02:08.922297-04	\N	county	department	Mombasa County Government	\N	{"county_code": "MOB", "asset_categories": ["ICT_EQUIPMENT", "FURNITURE_FITTINGS"], "can_assign_assets": true, "can_update_location": true}	\N	\N	0	\N	\N	password
user_007	\N	James	Ochieng	j.ochieng@tsc.go.ke	+254700789012	DEPT_TSC_REG	Regional Director	f	$2b$12$T6/XA5b1gu5w2Mp53OOUN.poAdDbj4BpU1gLuKPyBJlMnkF2jXkCS	role_006	active	2025-08-21 06:02:08.922297-04	\N	national	commission	Teachers Service Commission	\N	{"regional_scope": ["coast", "nyanza", "western"], "teacher_housing": true, "asset_categories": ["BUILDINGS", "ICT_EQUIPMENT", "MOTOR_VEHICLES"]}	\N	\N	0	\N	\N	password
user_008	\N	Agnes	Nyokabi	a.nyokabi@kplc.co.ke	+254700890123	DEPT_KPLC_001	Asset Custodian	f	$2b$12$T6/XA5b1gu5w2Mp53OOUN.poAdDbj4BpU1gLuKPyBJlMnkF2jXkCS	role_001	active	2025-08-21 06:02:08.922297-04	\N	national	state_corporation	Kenya Power and Lighting Company	\N	{"asset_categories": ["OTHER_INFRASTRUCTURE", "PLANT_MACHINERY", "MOTOR_VEHICLES"], "transmission_lines": true, "power_infrastructure": true}	\N	\N	0	\N	\N	password
\.


--
-- Data for Name: usertokens; Type: TABLE DATA; Schema: public; Owner: cage
--

COPY public.usertokens (jti, iat, user_id, exp, token, revoked) FROM stdin;
c4c64b84-1071-42c0-b3e2-71471808c9ec	2025-08-21 06:07:02.376081-04	user_001	2025-08-21 07:07:02.376015-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqLmthbWF1QHRyZWFzdXJ5LmdvLmtlIiwiaWQiOiJ1c2VyXzAwMSIsImV4cCI6MTc1NTc3NDQyMiwiaWF0IjoxNzU1NzcwODIyLCJqdGkiOiJjNGM2NGI4NC0xMDcxLTQyYzAtYjNlMi03MTQ3MTgwOGM5ZWMiLCJ0eXBlIjoiYWNjZXNzIn0.4XB7OyKMhojkpkwDgikLIFQ6uo1zzXiSH2b_aKjC1Lo	f
6b064d5e-5f16-4f43-b563-4427ead93503	2025-08-21 06:10:24.249119-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 07:10:24.249073-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU3NzQ2MjQsImlhdCI6MTc1NTc3MTAyNCwianRpIjoiNmIwNjRkNWUtNWYxNi00ZjQzLWI1NjMtNDQyN2VhZDkzNTAzIiwidHlwZSI6ImFjY2VzcyJ9.5linblxWa0V0Kzbx2pN5JN8Ybr5yOqUqcm5TI9As7aY	t
904433d5-0ac1-4178-b1a1-4aa6720361f6	2025-08-21 06:10:24.266007-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 07:10:24.26596-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU3NzQ2MjQsImlhdCI6MTc1NTc3MTAyNCwianRpIjoiOTA0NDMzZDUtMGFjMS00MTc4LWIxYTEtNGFhNjcyMDM2MWY2IiwidHlwZSI6InJlZnJlc2gifQ.jCinjg_F0ZSDL9V_OTCRa8nuYZlfKG_cRWRBGmIM91k	t
19538309-911e-4e14-9839-73a4a50a6c29	2025-08-21 06:11:35.212155-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 07:11:35.212083-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU3NzQ2OTUsImlhdCI6MTc1NTc3MTA5NSwianRpIjoiMTk1MzgzMDktOTExZS00ZTE0LTk4MzktNzNhNGE1MGE2YzI5IiwidHlwZSI6ImFjY2VzcyJ9.riGY5fLFztQ3HYkFK7RS-3iJKkHYlTGwsa3f-LSTL90	t
08fd560a-2d33-4caa-821b-f869031f021f	2025-08-21 05:12:19.743748-04	\N	2025-08-21 06:12:19.743664-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwidXNlcl9pZCI6IjgzY2ViZTNjLTBlMTctNGJlMC04MDg0LTgwYjUwMTg1M2MzOSIsImV4cCI6MTc1NTc3MTEzOSwiaWF0IjoxNzU1NzY3NTM5LCJqdGkiOiIwOGZkNTYwYS0yZDMzLTRjYWEtODIxYi1mODY5MDMxZjAyMWYiLCJ0eXBlIjoicmVmcmVzaCJ9.g4SubJdt5SMT9ZSvt--7buI--yC0o649jUSGQD3tsu8	t
c32a054c-5f0f-4a1d-b280-ec80b6b57161	2025-08-21 06:06:20.669457-04	\N	2025-08-21 07:06:20.669405-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwidXNlcl9pZCI6IjgzY2ViZTNjLTBlMTctNGJlMC04MDg0LTgwYjUwMTg1M2MzOSIsImV4cCI6MTc1NTc3NDM4MCwiaWF0IjoxNzU1NzcwNzgwLCJqdGkiOiJjMzJhMDU0Yy01ZjBmLTRhMWQtYjI4MC1lYzgwYjZiNTcxNjEiLCJ0eXBlIjoicmVmcmVzaCJ9.H8payEbxz1WHtL-MRVb9Q2oFL-r5Az94b3wNAIABIQE	t
213aa5be-afee-46a3-90de-0f1958bff56b	2025-08-21 06:07:02.392923-04	\N	2025-08-21 07:07:02.392881-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqLmthbWF1QHRyZWFzdXJ5LmdvLmtlIiwidXNlcl9pZCI6InVzZXJfMDAxIiwiZXhwIjoxNzU1Nzc0NDIyLCJpYXQiOjE3NTU3NzA4MjIsImp0aSI6IjIxM2FhNWJlLWFmZWUtNDZhMy05MGRlLTBmMTk1OGJmZjU2YiIsInR5cGUiOiJyZWZyZXNoIn0.3AACntPzln3w8qOpqhRXTJRBRtu8zXopoahH2jBg9ic	t
f20429e3-8637-4ead-aa8e-575d9064cb09	2025-08-21 06:11:35.237041-04	\N	2025-08-21 07:11:35.236995-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwidXNlcl9pZCI6IjgzY2ViZTNjLTBlMTctNGJlMC04MDg0LTgwYjUwMTg1M2MzOSIsImV4cCI6MTc1NTc3NDY5NSwiaWF0IjoxNzU1NzcxMDk1LCJqdGkiOiJmMjA0MjllMy04NjM3LTRlYWQtYWE4ZS01NzVkOTA2NGNiMDkiLCJ0eXBlIjoicmVmcmVzaCJ9.89FN_PIVM9fZt72FmSUj984XqpBFc1c915_p1DXR5p8	t
2450521b-ae07-41c3-b51f-44d6c0837f7d	2025-08-21 06:18:39.409518-04	\N	2025-08-21 07:11:34.409476-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOm51bGwsImV4cCI6MTc1NTc3NDY5NCwiaWF0IjoxNzU1NzcxNTE5LCJqdGkiOiIyNDUwNTIxYi1hZTA3LTQxYzMtYjUxZi00NGQ2YzA4MzdmN2QiLCJ0eXBlIjoiYWNjZXNzIn0.8x8RaZpBsL1JYGf0FtLuC6Wvw1YeW8XiyhhKrsYKY_g	f
46a63ad2-a493-472e-8704-260012395fc7	2025-08-21 06:18:39.5244-04	\N	2025-08-21 07:11:34.524351-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOm51bGwsImV4cCI6MTc1NTc3NDY5NCwiaWF0IjoxNzU1NzcxNTE5LCJqdGkiOiI0NmE2M2FkMi1hNDkzLTQ3MmUtODcwNC0yNjAwMTIzOTVmYzciLCJ0eXBlIjoicmVmcmVzaCJ9.Zw7dJnH5-GIDeFdQhuHQNMzQbDgApBHSh2WsopWyRZs	f
d6457d5e-baed-4bd9-923c-9dc2540c307d	2025-08-21 06:24:45.562084-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 07:24:45.562024-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU3NzU0ODUsImlhdCI6MTc1NTc3MTg4NSwianRpIjoiZDY0NTdkNWUtYmFlZC00YmQ5LTkyM2MtOWRjMjU0MGMzMDdkIiwidHlwZSI6ImFjY2VzcyJ9.NVioaWDOiEYI6B1mD_LX-9q329pXlKPjxTfYo9tBDzM	f
fa891b75-1c8d-403f-9eca-ec23aaa21c11	2025-08-21 06:24:45.594406-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 07:24:45.594359-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU3NzU0ODUsImlhdCI6MTc1NTc3MTg4NSwianRpIjoiZmE4OTFiNzUtMWM4ZC00MDNmLTllY2EtZWMyM2FhYTIxYzExIiwidHlwZSI6InJlZnJlc2gifQ.9dGQS4fqsS4YMvTSn0sRmSwfm89xxMIlolPOCGRa4zE	f
62073d8c-6832-4273-b881-e827fb28f16f	2025-08-21 06:29:59.544771-04	user_001	2025-08-21 07:29:59.544648-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqLmthbWF1QHRyZWFzdXJ5LmdvLmtlIiwiaWQiOiJ1c2VyXzAwMSIsImV4cCI6MTc1NTc3NTc5OSwiaWF0IjoxNzU1NzcyMTk5LCJqdGkiOiI2MjA3M2Q4Yy02ODMyLTQyNzMtYjg4MS1lODI3ZmIyOGYxNmYiLCJ0eXBlIjoiYWNjZXNzIn0.sELolFRW2RrLAwnSV1X0if1BkxfnnNAzADHWTJa33WE	f
f6d2a78a-b085-4d3f-bf64-4691dff0b1fd	2025-08-21 06:29:59.586105-04	user_001	2025-08-21 07:29:59.586057-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJqLmthbWF1QHRyZWFzdXJ5LmdvLmtlIiwiaWQiOiJ1c2VyXzAwMSIsImV4cCI6MTc1NTc3NTc5OSwiaWF0IjoxNzU1NzcyMTk5LCJqdGkiOiJmNmQyYTc4YS1iMDg1LTRkM2YtYmY2NC00NjkxZGZmMGIxZmQiLCJ0eXBlIjoicmVmcmVzaCJ9.2DUhxUTCWVXOFEz3MGwomToiex5WpPHQN24gVlliO-c	f
18c4c371-0eae-48a3-a5e9-8321441a54cb	2025-08-21 07:32:50.949385-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 08:32:50.949316-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU3Nzk1NzAsImlhdCI6MTc1NTc3NTk3MCwianRpIjoiMThjNGMzNzEtMGVhZS00OGEzLWE1ZTktODMyMTQ0MWE1NGNiIiwidHlwZSI6ImFjY2VzcyJ9.8XlEVZ6lnKVeuGz3u68GHyVjUENQhRxfHUj2akmNf9U	f
fb9dacf8-2aff-442b-a9b1-939127965224	2025-08-21 07:32:51.007222-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 08:32:51.007173-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU3Nzk1NzEsImlhdCI6MTc1NTc3NTk3MSwianRpIjoiZmI5ZGFjZjgtMmFmZi00NDJiLWE5YjEtOTM5MTI3OTY1MjI0IiwidHlwZSI6InJlZnJlc2gifQ.mp6IjW5ByKr-S2QMB8AbNnDrf6NPeU9T59wXTT5GSqE	f
326bf4ce-6f5e-4c3a-b239-e76e9cd530ff	2025-08-21 15:13:57.761806-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 16:13:57.761747-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU4MDcyMzcsImlhdCI6MTc1NTgwMzYzNywianRpIjoiMzI2YmY0Y2UtNmY1ZS00YzNhLWIyMzktZTc2ZTljZDUzMGZmIiwidHlwZSI6ImFjY2VzcyJ9.cG6ybuh3YjVHoMmoapqaTPdMoJDVBPN-6SL7IZpUqGo	f
2db378cb-0eab-410e-af58-235d489e3039	2025-08-21 15:13:57.82241-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 16:13:57.822361-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU4MDcyMzcsImlhdCI6MTc1NTgwMzYzNywianRpIjoiMmRiMzc4Y2ItMGVhYi00MTBlLWFmNTgtMjM1ZDQ4OWUzMDM5IiwidHlwZSI6InJlZnJlc2gifQ.JDHv8C6SXxjavzAf9E06IUYttgTOjFU8OPLKkY4d3ok	f
22728c09-65b3-49c2-9c15-85300ca7f472	2025-08-21 15:14:32.82464-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 16:14:32.824582-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU4MDcyNzIsImlhdCI6MTc1NTgwMzY3MiwianRpIjoiMjI3MjhjMDktNjViMy00OWMyLTljMTUtODUzMDBjYTdmNDcyIiwidHlwZSI6ImFjY2VzcyJ9.Q6Av-B7MuAR0BgS2LZSl62YZzJQaXu9fgt69l6T45cA	f
1c42953f-21fd-4dc7-933f-75dcc3b595c0	2025-08-21 15:14:32.849261-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 16:14:32.849211-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU4MDcyNzIsImlhdCI6MTc1NTgwMzY3MiwianRpIjoiMWM0Mjk1M2YtMjFmZC00ZGM3LTkzM2YtNzVkY2MzYjU5NWMwIiwidHlwZSI6InJlZnJlc2gifQ.xvZmvJJAIXDkGr_qWxKGmbbydZlVWe3gefiFI2PXlho	f
1342a331-0c85-43b9-bf99-d94c06ed11c8	2025-08-21 15:14:58.825329-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 16:14:58.825282-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU4MDcyOTgsImlhdCI6MTc1NTgwMzY5OCwianRpIjoiMTM0MmEzMzEtMGM4NS00M2I5LWJmOTktZDk0YzA2ZWQxMWM4IiwidHlwZSI6ImFjY2VzcyJ9.tXZMQ-wAEzbY2Sg7-M_ywNdd51z8GAPPozZhiYRX7_8	f
a11b18f4-d0b9-4270-8578-2827e3d17950	2025-08-21 15:14:58.846925-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 16:14:58.846882-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU4MDcyOTgsImlhdCI6MTc1NTgwMzY5OCwianRpIjoiYTExYjE4ZjQtZDBiOS00MjcwLTg1NzgtMjgyN2UzZDE3OTUwIiwidHlwZSI6InJlZnJlc2gifQ.ASyaEfLybZEUcoqWbmJgilyGWkPAhkDCpP3KE7yulVE	f
c35eec5a-623f-42cb-8f37-fc6304b73ad7	2025-08-21 15:54:21.315747-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 16:54:21.31569-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU4MDk2NjEsImlhdCI6MTc1NTgwNjA2MSwianRpIjoiYzM1ZWVjNWEtNjIzZi00MmNiLThmMzctZmM2MzA0YjczYWQ3IiwidHlwZSI6ImFjY2VzcyJ9.6YsuZ6TK2sS5pmr8UYhcSQCAjOf1vfF0ArMeEZhcNCk	f
91cb6b05-6587-4c06-8da6-c2e1ff0ea1c6	2025-08-21 15:54:21.352872-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 16:54:21.352821-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU4MDk2NjEsImlhdCI6MTc1NTgwNjA2MSwianRpIjoiOTFjYjZiMDUtNjU4Ny00YzA2LThkYTYtYzJlMWZmMGVhMWM2IiwidHlwZSI6InJlZnJlc2gifQ.VadnKxJWkUCB38wcri63Q8w3k9K7gQ2ExdhtHHZ9C6E	f
ea851dae-7e2f-44a2-886a-d5b4b08120f2	2025-08-21 17:05:16.161294-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 18:05:16.161241-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU4MTM5MTYsImlhdCI6MTc1NTgxMDMxNiwianRpIjoiZWE4NTFkYWUtN2UyZi00NGEyLTg4NmEtZDViNGIwODEyMGYyIiwidHlwZSI6ImFjY2VzcyJ9.She9eKIDt3zUq969h23gFLtCshaar9BvjoIeviehJMk	f
8b127970-280a-4505-a94d-d0e85acc12db	2025-08-21 17:05:16.196284-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 18:05:16.196232-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU4MTM5MTYsImlhdCI6MTc1NTgxMDMxNiwianRpIjoiOGIxMjc5NzAtMjgwYS00NTA1LWE5NGQtZDBlODVhY2MxMmRiIiwidHlwZSI6InJlZnJlc2gifQ.iI3fKzhC-SbjzWNgtwksFlPbdr0FkaYT2OTi121HcK4	f
2258e385-36a9-4951-b4d2-34102d2eedea	2025-08-21 17:22:26.793704-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 18:22:26.793642-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU4MTQ5NDYsImlhdCI6MTc1NTgxMTM0NiwianRpIjoiMjI1OGUzODUtMzZhOS00OTUxLWI0ZDItMzQxMDJkMmVlZGVhIiwidHlwZSI6ImFjY2VzcyJ9.HgYOJINMgCoZdZGI-Ta0Eo9UKbHZmU1VjXMYdzvHEVo	f
ab6f3654-0f17-4d00-946e-80ef8b86d4ed	2025-08-21 17:22:26.842421-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 18:22:26.842371-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU4MTQ5NDYsImlhdCI6MTc1NTgxMTM0NiwianRpIjoiYWI2ZjM2NTQtMGYxNy00ZDAwLTk0NmUtODBlZjhiODZkNGVkIiwidHlwZSI6InJlZnJlc2gifQ.kyMxKm0sDw23I8oFm9ocYtV1Q2gY3a0WiSG0B6TgOj8	f
e9f16059-f66e-47d6-9467-a07e46b59467	2025-08-21 17:29:02.421958-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 18:29:02.421906-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU4MTUzNDIsImlhdCI6MTc1NTgxMTc0MiwianRpIjoiZTlmMTYwNTktZjY2ZS00N2Q2LTk0NjctYTA3ZTQ2YjU5NDY3IiwidHlwZSI6ImFjY2VzcyJ9.LLxmqfHgnk-oBIkp43bvIfi0khRQihni1GCaroD9CxA	f
94e44125-7f78-498f-8373-382a5fe6a4ea	2025-08-21 17:29:02.453154-04	83cebe3c-0e17-4be0-8084-80b501853c39	2025-08-21 18:29:02.453108-04	eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaWQiOiI4M2NlYmUzYy0wZTE3LTRiZTAtODA4NC04MGI1MDE4NTNjMzkiLCJleHAiOjE3NTU4MTUzNDIsImlhdCI6MTc1NTgxMTc0MiwianRpIjoiOTRlNDQxMjUtN2Y3OC00OThmLTgzNzMtMzgyYTVmZTZhNGVhIiwidHlwZSI6InJlZnJlc2gifQ.807CL2FtcAGuvp_lBJmx6rX5WCzvtFPLf_gK7HRD5HI	f
\.


--
-- Name: abac_policies_id_seq; Type: SEQUENCE SET; Schema: public; Owner: cage
--

SELECT pg_catalog.setval('public.abac_policies_id_seq', 1, false);


--
-- Name: abac_policies abac_policies_pkey; Type: CONSTRAINT; Schema: public; Owner: cage
--

ALTER TABLE ONLY public.abac_policies
    ADD CONSTRAINT abac_policies_pkey PRIMARY KEY (id);


--
-- Name: activity_logs activity_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: cage
--

ALTER TABLE ONLY public.activity_logs
    ADD CONSTRAINT activity_logs_pkey PRIMARY KEY (id);


--
-- Name: departments departments_pkey; Type: CONSTRAINT; Schema: public; Owner: cage
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_pkey PRIMARY KEY (dept_id);


--
-- Name: roles roles_pkey; Type: CONSTRAINT; Schema: public; Owner: cage
--

ALTER TABLE ONLY public.roles
    ADD CONSTRAINT roles_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: cage
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: usertokens usertokens_pkey; Type: CONSTRAINT; Schema: public; Owner: cage
--

ALTER TABLE ONLY public.usertokens
    ADD CONSTRAINT usertokens_pkey PRIMARY KEY (jti);


--
-- Name: ix_departments_dept_id; Type: INDEX; Schema: public; Owner: cage
--

CREATE INDEX ix_departments_dept_id ON public.departments USING btree (dept_id);


--
-- Name: ix_roles_id; Type: INDEX; Schema: public; Owner: cage
--

CREATE INDEX ix_roles_id ON public.roles USING btree (id);


--
-- Name: ix_roles_name; Type: INDEX; Schema: public; Owner: cage
--

CREATE UNIQUE INDEX ix_roles_name ON public.roles USING btree (name);


--
-- Name: ix_users_email; Type: INDEX; Schema: public; Owner: cage
--

CREATE UNIQUE INDEX ix_users_email ON public.users USING btree (email);


--
-- Name: ix_users_id; Type: INDEX; Schema: public; Owner: cage
--

CREATE INDEX ix_users_id ON public.users USING btree (id);


--
-- Name: ix_users_phone_number; Type: INDEX; Schema: public; Owner: cage
--

CREATE UNIQUE INDEX ix_users_phone_number ON public.users USING btree (phone_number);


--
-- Name: ix_usertokens_jti; Type: INDEX; Schema: public; Owner: cage
--

CREATE INDEX ix_usertokens_jti ON public.usertokens USING btree (jti);


--
-- Name: activity_logs activity_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cage
--

ALTER TABLE ONLY public.activity_logs
    ADD CONSTRAINT activity_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: departments departments_parent_dept_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cage
--

ALTER TABLE ONLY public.departments
    ADD CONSTRAINT departments_parent_dept_id_fkey FOREIGN KEY (parent_dept_id) REFERENCES public.departments(dept_id);


--
-- Name: users users_department_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cage
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_department_id_fkey FOREIGN KEY (department_id) REFERENCES public.departments(dept_id);


--
-- Name: users users_roles_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cage
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_roles_fkey FOREIGN KEY (role_id) REFERENCES public.roles(id);


--
-- Name: usertokens usertokens_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: cage
--

ALTER TABLE ONLY public.usertokens
    ADD CONSTRAINT usertokens_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: SCHEMA public; Type: ACL; Schema: -; Owner: klax
--

REVOKE USAGE ON SCHEMA public FROM PUBLIC;
GRANT ALL ON SCHEMA public TO postgres;
GRANT ALL ON SCHEMA public TO PUBLIC;


--
-- Name: TABLE abac_policies; Type: ACL; Schema: public; Owner: cage
--

GRANT SELECT,INSERT,DELETE,UPDATE ON TABLE public.abac_policies TO klax;


--
-- Name: SEQUENCE abac_policies_id_seq; Type: ACL; Schema: public; Owner: cage
--

GRANT ALL ON SEQUENCE public.abac_policies_id_seq TO klax;


--
-- Name: TABLE activity_logs; Type: ACL; Schema: public; Owner: cage
--

GRANT ALL ON TABLE public.activity_logs TO klax;


--
-- Name: TABLE departments; Type: ACL; Schema: public; Owner: cage
--

GRANT ALL ON TABLE public.departments TO klax;


--
-- Name: TABLE roles; Type: ACL; Schema: public; Owner: cage
--

GRANT ALL ON TABLE public.roles TO klax;


--
-- Name: TABLE users; Type: ACL; Schema: public; Owner: cage
--

GRANT ALL ON TABLE public.users TO klax;


--
-- Name: TABLE usertokens; Type: ACL; Schema: public; Owner: cage
--

GRANT ALL ON TABLE public.usertokens TO klax;


--
-- Name: DEFAULT PRIVILEGES FOR SEQUENCES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON SEQUENCES TO klax;


--
-- Name: DEFAULT PRIVILEGES FOR TABLES; Type: DEFAULT ACL; Schema: public; Owner: postgres
--

ALTER DEFAULT PRIVILEGES FOR ROLE postgres IN SCHEMA public GRANT ALL ON TABLES TO klax;


--
-- PostgreSQL database dump complete
--

