--
-- PostgreSQL database dump
--

\restrict xyH6C2UTXsqfMaVo82sY2Schq6TlVJuLcNBD4BHkVrvL44vFEk7rFhNZLRqV4Pu

-- Dumped from database version 18.1
-- Dumped by pg_dump version 18.1

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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: accounts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.accounts (
    account_id integer NOT NULL,
    user_id integer,
    account_name character varying(100) NOT NULL,
    account_type character varying(50) NOT NULL,
    balance numeric(15,2) DEFAULT 0.00,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.accounts OWNER TO postgres;

--
-- Name: accounts_account_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.accounts_account_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.accounts_account_id_seq OWNER TO postgres;

--
-- Name: accounts_account_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.accounts_account_id_seq OWNED BY public.accounts.account_id;


--
-- Name: categories; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.categories (
    category_id integer NOT NULL,
    user_id integer,
    category_name character varying(100) NOT NULL,
    category_type character varying(10) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT categories_category_type_check CHECK (((category_type)::text = ANY ((ARRAY['income'::character varying, 'expense'::character varying])::text[])))
);


ALTER TABLE public.categories OWNER TO postgres;

--
-- Name: categories_category_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.categories_category_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.categories_category_id_seq OWNER TO postgres;

--
-- Name: categories_category_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.categories_category_id_seq OWNED BY public.categories.category_id;


--
-- Name: chat_history; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chat_history (
    chat_id integer NOT NULL,
    user_id integer NOT NULL,
    message_text text NOT NULL,
    message_type character varying(10) NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    session_id integer,
    CONSTRAINT chat_history_message_type_check CHECK (((message_type)::text = ANY ((ARRAY['user'::character varying, 'ai'::character varying])::text[])))
);


ALTER TABLE public.chat_history OWNER TO postgres;

--
-- Name: TABLE chat_history; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.chat_history IS '€бв®аЁп з в®ў Ї®«м§®ў вҐ«Ґ© б AI-б®ўҐв­ЁЄ®¬';


--
-- Name: COLUMN chat_history.chat_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.chat_history.chat_id IS '“­ЁЄ «м­л© Ё¤Ґ­вЁдЁЄ в®а б®®ЎйҐ­Ёп';


--
-- Name: COLUMN chat_history.user_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.chat_history.user_id IS 'ID Ї®«м§®ў вҐ«п (бўп§м б users)';


--
-- Name: COLUMN chat_history.message_text; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.chat_history.message_text IS '’ҐЄбв б®®ЎйҐ­Ёп';


--
-- Name: COLUMN chat_history.message_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.chat_history.message_type IS '’ЁЇ б®®ЎйҐ­Ёп: user Ё«Ё ai';


--
-- Name: COLUMN chat_history.created_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.chat_history.created_at IS '„ в  Ё ўаҐ¬п б®§¤ ­Ёп б®®ЎйҐ­Ёп';


--
-- Name: chat_history_chat_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.chat_history_chat_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.chat_history_chat_id_seq OWNER TO postgres;

--
-- Name: chat_history_chat_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.chat_history_chat_id_seq OWNED BY public.chat_history.chat_id;


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notifications (
    notification_id integer NOT NULL,
    user_id integer,
    message text NOT NULL,
    type character varying(50) DEFAULT 'info'::character varying,
    is_read boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.notifications OWNER TO postgres;

--
-- Name: notifications_notification_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notifications_notification_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notifications_notification_id_seq OWNER TO postgres;

--
-- Name: notifications_notification_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notifications_notification_id_seq OWNED BY public.notifications.notification_id;


--
-- Name: transaction_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transaction_logs (
    log_id integer NOT NULL,
    transaction_id integer,
    action character varying(20) NOT NULL,
    amount numeric(15,2) NOT NULL,
    transaction_type character varying(10) NOT NULL,
    old_balance numeric(15,2) NOT NULL,
    new_balance numeric(15,2) NOT NULL,
    user_id integer NOT NULL,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.transaction_logs OWNER TO postgres;

--
-- Name: transaction_logs_log_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.transaction_logs_log_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.transaction_logs_log_id_seq OWNER TO postgres;

--
-- Name: transaction_logs_log_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.transaction_logs_log_id_seq OWNED BY public.transaction_logs.log_id;


--
-- Name: transactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transactions (
    transaction_id integer NOT NULL,
    user_id integer,
    account_id integer,
    category_id integer,
    amount numeric(15,2) NOT NULL,
    transaction_type character varying(10) NOT NULL,
    description text,
    transaction_date timestamp with time zone NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT transactions_transaction_type_check CHECK (((transaction_type)::text = ANY ((ARRAY['income'::character varying, 'expense'::character varying])::text[])))
);


ALTER TABLE public.transactions OWNER TO postgres;

--
-- Name: transactions_transaction_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.transactions_transaction_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.transactions_transaction_id_seq OWNER TO postgres;

--
-- Name: transactions_transaction_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.transactions_transaction_id_seq OWNED BY public.transactions.transaction_id;


--
-- Name: user_profiles; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_profiles (
    profile_id integer NOT NULL,
    user_id integer,
    full_name character varying(100),
    currency character varying(10) DEFAULT 'KZT'::character varying
);


ALTER TABLE public.user_profiles OWNER TO postgres;

--
-- Name: user_profiles_profile_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_profiles_profile_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_profiles_profile_id_seq OWNER TO postgres;

--
-- Name: user_profiles_profile_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_profiles_profile_id_seq OWNED BY public.user_profiles.profile_id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    user_id integer NOT NULL,
    username character varying(50) NOT NULL,
    email character varying(100) NOT NULL,
    password_hash character varying(255) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    role character varying(20) DEFAULT 'user'::character varying
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_user_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_user_id_seq OWNER TO postgres;

--
-- Name: users_user_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_user_id_seq OWNED BY public.users.user_id;


--
-- Name: accounts account_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts ALTER COLUMN account_id SET DEFAULT nextval('public.accounts_account_id_seq'::regclass);


--
-- Name: categories category_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categories ALTER COLUMN category_id SET DEFAULT nextval('public.categories_category_id_seq'::regclass);


--
-- Name: chat_history chat_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_history ALTER COLUMN chat_id SET DEFAULT nextval('public.chat_history_chat_id_seq'::regclass);


--
-- Name: notifications notification_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications ALTER COLUMN notification_id SET DEFAULT nextval('public.notifications_notification_id_seq'::regclass);


--
-- Name: transaction_logs log_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transaction_logs ALTER COLUMN log_id SET DEFAULT nextval('public.transaction_logs_log_id_seq'::regclass);


--
-- Name: transactions transaction_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions ALTER COLUMN transaction_id SET DEFAULT nextval('public.transactions_transaction_id_seq'::regclass);


--
-- Name: user_profiles profile_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_profiles ALTER COLUMN profile_id SET DEFAULT nextval('public.user_profiles_profile_id_seq'::regclass);


--
-- Name: users user_id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN user_id SET DEFAULT nextval('public.users_user_id_seq'::regclass);


--
-- Data for Name: accounts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.accounts (account_id, user_id, account_name, account_type, balance, created_at) FROM stdin;
15	25	Основной счет	cash	0.00	2025-12-18 09:47:00.466353+05
7	15	Основной счет	cash	0.00	2025-12-15 21:25:01.170616+05
5	13	Основной счет	cash	-1234.00	2025-12-15 17:24:28.757687+05
4	12	Основной счет	cash	0.00	2025-12-15 17:24:03.866251+05
13	23	Основной счет	cash	0.00	2025-12-17 08:10:38.901936+05
\.


--
-- Data for Name: categories; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.categories (category_id, user_id, category_name, category_type, created_at) FROM stdin;
221	13	Инвестиция	income	2025-12-17 20:40:30.092095+05
223	25	Продукты	expense	2025-12-18 09:47:00.466353+05
224	25	Транспорт	expense	2025-12-18 09:47:00.466353+05
225	25	Развлечения	expense	2025-12-18 09:47:00.466353+05
226	25	Комм. услуги	expense	2025-12-18 09:47:00.466353+05
227	25	Покупки	expense	2025-12-18 09:47:00.466353+05
228	25	Здоровье	expense	2025-12-18 09:47:00.466353+05
229	25	Образование	expense	2025-12-18 09:47:00.466353+05
230	25	Ресторан	expense	2025-12-18 09:47:00.466353+05
231	25	Одежда	expense	2025-12-18 09:47:00.466353+05
232	25	Связь	expense	2025-12-18 09:47:00.466353+05
233	25	Спорт	expense	2025-12-18 09:47:00.466353+05
234	25	Путешествия	expense	2025-12-18 09:47:00.466353+05
235	25	Подарки	expense	2025-12-18 09:47:00.466353+05
236	25	Красота	expense	2025-12-18 09:47:00.466353+05
237	25	Автомобиль	expense	2025-12-18 09:47:00.466353+05
238	25	Доходы	income	2025-12-18 09:47:00.466353+05
239	25	Другое	expense	2025-12-18 09:47:00.466353+05
23	12	Продукты	expense	2025-12-15 17:24:03.866251+05
24	12	Транспорт	expense	2025-12-15 17:24:03.866251+05
25	12	Развлечения	expense	2025-12-15 17:24:03.866251+05
26	12	Комм. услуги	expense	2025-12-15 17:24:03.866251+05
27	12	Покупки	expense	2025-12-15 17:24:03.866251+05
28	12	Здоровье	expense	2025-12-15 17:24:03.866251+05
29	12	Образование	expense	2025-12-15 17:24:03.866251+05
30	12	Ресторан	expense	2025-12-15 17:24:03.866251+05
31	12	Одежда	expense	2025-12-15 17:24:03.866251+05
32	12	Связь	expense	2025-12-15 17:24:03.866251+05
33	12	Спорт	expense	2025-12-15 17:24:03.866251+05
34	12	Путешествия	expense	2025-12-15 17:24:03.866251+05
35	12	Подарки	expense	2025-12-15 17:24:03.866251+05
36	12	Красота	expense	2025-12-15 17:24:03.866251+05
37	12	Автомобиль	expense	2025-12-15 17:24:03.866251+05
38	12	Доходы	income	2025-12-15 17:24:03.866251+05
39	12	Другое	expense	2025-12-15 17:24:03.866251+05
40	13	Продукты	expense	2025-12-15 17:24:28.757687+05
41	13	Транспорт	expense	2025-12-15 17:24:28.757687+05
42	13	Развлечения	expense	2025-12-15 17:24:28.757687+05
43	13	Комм. услуги	expense	2025-12-15 17:24:28.757687+05
44	13	Покупки	expense	2025-12-15 17:24:28.757687+05
45	13	Здоровье	expense	2025-12-15 17:24:28.757687+05
46	13	Образование	expense	2025-12-15 17:24:28.757687+05
47	13	Ресторан	expense	2025-12-15 17:24:28.757687+05
48	13	Одежда	expense	2025-12-15 17:24:28.757687+05
49	13	Связь	expense	2025-12-15 17:24:28.757687+05
50	13	Спорт	expense	2025-12-15 17:24:28.757687+05
51	13	Путешествия	expense	2025-12-15 17:24:28.757687+05
52	13	Подарки	expense	2025-12-15 17:24:28.757687+05
53	13	Красота	expense	2025-12-15 17:24:28.757687+05
54	13	Автомобиль	expense	2025-12-15 17:24:28.757687+05
55	13	Доходы	income	2025-12-15 17:24:28.757687+05
56	13	Другое	expense	2025-12-15 17:24:28.757687+05
74	15	Продукты	expense	2025-12-15 21:25:01.170616+05
75	15	Транспорт	expense	2025-12-15 21:25:01.170616+05
76	15	Развлечения	expense	2025-12-15 21:25:01.170616+05
77	15	Комм. услуги	expense	2025-12-15 21:25:01.170616+05
78	15	Покупки	expense	2025-12-15 21:25:01.170616+05
79	15	Здоровье	expense	2025-12-15 21:25:01.170616+05
80	15	Образование	expense	2025-12-15 21:25:01.170616+05
81	15	Ресторан	expense	2025-12-15 21:25:01.170616+05
82	15	Одежда	expense	2025-12-15 21:25:01.170616+05
83	15	Связь	expense	2025-12-15 21:25:01.170616+05
84	15	Спорт	expense	2025-12-15 21:25:01.170616+05
85	15	Путешествия	expense	2025-12-15 21:25:01.170616+05
86	15	Подарки	expense	2025-12-15 21:25:01.170616+05
87	15	Красота	expense	2025-12-15 21:25:01.170616+05
88	15	Автомобиль	expense	2025-12-15 21:25:01.170616+05
89	15	Доходы	income	2025-12-15 21:25:01.170616+05
90	15	Другое	expense	2025-12-15 21:25:01.170616+05
222	13	Фриланс	income	2025-12-17 21:02:36.953902+05
240	25	Еда	expense	2025-12-18 09:50:03.593531+05
162	13	Еда	expense	2025-12-16 19:20:33.108628+05
163	13	Зарплата	income	2025-12-16 19:20:41.651546+05
164	13	Жилье	expense	2025-12-16 19:56:00.341188+05
165	13	Сбережения	income	2025-12-16 20:03:03.830181+05
183	23	Продукты	expense	2025-12-17 08:10:38.901936+05
184	23	Транспорт	expense	2025-12-17 08:10:38.901936+05
185	23	Развлечения	expense	2025-12-17 08:10:38.901936+05
186	23	Комм. услуги	expense	2025-12-17 08:10:38.901936+05
187	23	Покупки	expense	2025-12-17 08:10:38.901936+05
188	23	Здоровье	expense	2025-12-17 08:10:38.901936+05
189	23	Образование	expense	2025-12-17 08:10:38.901936+05
190	23	Ресторан	expense	2025-12-17 08:10:38.901936+05
191	23	Одежда	expense	2025-12-17 08:10:38.901936+05
192	23	Связь	expense	2025-12-17 08:10:38.901936+05
193	23	Спорт	expense	2025-12-17 08:10:38.901936+05
194	23	Путешествия	expense	2025-12-17 08:10:38.901936+05
195	23	Подарки	expense	2025-12-17 08:10:38.901936+05
196	23	Красота	expense	2025-12-17 08:10:38.901936+05
197	23	Автомобиль	expense	2025-12-17 08:10:38.901936+05
198	23	Доходы	income	2025-12-17 08:10:38.901936+05
199	23	Другое	expense	2025-12-17 08:10:38.901936+05
200	13	Дивиденды	income	2025-12-17 08:23:31.270738+05
201	13	Подарок	income	2025-12-17 10:48:44.176302+05
\.


--
-- Data for Name: chat_history; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.chat_history (chat_id, user_id, message_text, message_type, created_at, session_id) FROM stdin;
\.


--
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notifications (notification_id, user_id, message, type, is_read, created_at) FROM stdin;
3	13	Новый доход: 12345 на сумму ₸25342.00	transaction	t	2025-12-17 08:23:31.364682+05
6	13	Новый доход: 1234 на сумму ₸2500.00	transaction	t	2025-12-17 10:48:44.236273+05
5	13	Новый доход: 2334546 на сумму ₸25000.00	transaction	t	2025-12-17 10:24:38.615929+05
4	13	Новый доход: 23232 на сумму ₸25000.00	transaction	t	2025-12-17 10:23:41.265657+05
11	13	Новый расход: 1234 на сумму ₸1234.00	transaction	t	2025-12-17 17:44:24.418195+05
12	13	Новый расход: 1234 на сумму ₸2500.00	transaction	t	2025-12-17 21:02:30.843897+05
7	13	Новый расход: Без описания на сумму ₸23123.00	transaction	t	2025-12-17 10:48:49.839333+05
1	13	Новый доход: 1234 на сумму ₸2500.00	transaction	t	2025-12-16 20:03:03.899241+05
2	13	Новый расход: 1234 на сумму ₸1234.00	transaction	t	2025-12-16 23:13:57.615307+05
14	25	Новый расход: Продукты на сумму ₸2500.00	transaction	f	2025-12-18 09:50:03.691008+05
15	15	Новый расход: hdbcbc на сумму ₸2500.00	transaction	f	2025-12-18 09:53:37.724867+05
13	13	Новый доход: 1234 на сумму ₸2134.00	transaction	t	2025-12-17 21:02:37.01226+05
16	13	Новый расход: 1234 на сумму ₸1234.00	transaction	f	2025-12-18 10:11:40.023592+05
17	13	Новый расход: 1234 на сумму ₸1234.00	transaction	f	2025-12-18 10:37:48.623644+05
\.


--
-- Data for Name: transaction_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.transaction_logs (log_id, transaction_id, action, amount, transaction_type, old_balance, new_balance, user_id, created_at) FROM stdin;
1	25	delete	25342.00	income	16362.00	-8980.00	13	2025-12-17 10:15:37.499425
2	24	delete	1234.00	expense	-8980.00	-7746.00	13	2025-12-17 10:15:50.729972
3	23	delete	2500.00	income	-7746.00	-10246.00	13	2025-12-17 10:16:07.921401
4	22	delete	1234.00	expense	-10246.00	-9012.00	13	2025-12-17 10:17:30.171977
5	19	delete	2222.00	income	-9012.00	-11234.00	13	2025-12-17 10:17:33.345181
6	21	delete	1234.00	expense	-11234.00	-10000.00	13	2025-12-17 10:19:04.396855
7	20	delete	2500.00	expense	-10000.00	-7500.00	13	2025-12-17 10:23:29.288669
8	26	delete	25000.00	income	17500.00	-7500.00	13	2025-12-17 10:24:31.401799
9	29	delete	23123.00	expense	-3123.00	20000.00	13	2025-12-17 10:48:54.846142
10	33	delete	1234.00	expense	18766.00	20000.00	13	2025-12-17 20:40:07.310381
11	37	delete	2500.00	expense	-2500.00	0.00	15	2025-12-18 09:53:40.291753
\.


--
-- Data for Name: transactions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.transactions (transaction_id, user_id, account_id, category_id, amount, transaction_type, description, transaction_date, created_at) FROM stdin;
39	13	5	164	1234.00	expense	1234	2025-12-18 10:37:00+05	2025-12-18 10:37:48.533029+05
\.


--
-- Data for Name: user_profiles; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_profiles (profile_id, user_id, full_name, currency) FROM stdin;
2	12	123456	KZT
3	13	erkebulan	KZT
5	15	maria	KZT
11	23	maria_admin	KZT
13	25	1234	KZT
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (user_id, username, email, password_hash, created_at, role) FROM stdin;
13	erkebulan	erkebulan@gmail.com	8d969eef6ecad3c29a3a629280e686cf0c3f5d5a86aff3ca12020c923adc6c92	2025-12-15 17:24:28.757687+05	admin
12	123456	1234@gmail.ocm	03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4	2025-12-15 17:24:03.866251+05	admin
15	maria	maria@gmail.com	f37f3f2b0dc57a86dee4ba6ff855283bb4d2f0dea1c5bd1b708853444c2ffcec	2025-12-15 21:25:01.170616+05	admin
23	maria_admin	maria_admin@gmail.com	03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4	2025-12-17 08:10:38.901936+05	admin
25	1234	1234@gmail.com	03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4	2025-12-18 09:47:00.466353+05	user
\.


--
-- Name: accounts_account_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.accounts_account_id_seq', 15, true);


--
-- Name: categories_category_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.categories_category_id_seq', 240, true);


--
-- Name: chat_history_chat_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.chat_history_chat_id_seq', 163, true);


--
-- Name: notifications_notification_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.notifications_notification_id_seq', 17, true);


--
-- Name: transaction_logs_log_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.transaction_logs_log_id_seq', 11, true);


--
-- Name: transactions_transaction_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.transactions_transaction_id_seq', 39, true);


--
-- Name: user_profiles_profile_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_profiles_profile_id_seq', 13, true);


--
-- Name: users_user_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_user_id_seq', 25, true);


--
-- Name: accounts accounts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_pkey PRIMARY KEY (account_id);


--
-- Name: accounts accounts_user_id_account_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_user_id_account_name_key UNIQUE (user_id, account_name);


--
-- Name: categories categories_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_pkey PRIMARY KEY (category_id);


--
-- Name: categories categories_user_id_category_name_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_user_id_category_name_key UNIQUE (user_id, category_name);


--
-- Name: chat_history chat_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_history
    ADD CONSTRAINT chat_history_pkey PRIMARY KEY (chat_id);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (notification_id);


--
-- Name: transaction_logs transaction_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transaction_logs
    ADD CONSTRAINT transaction_logs_pkey PRIMARY KEY (log_id);


--
-- Name: transactions transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_pkey PRIMARY KEY (transaction_id);


--
-- Name: user_profiles user_profiles_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_pkey PRIMARY KEY (profile_id);


--
-- Name: user_profiles user_profiles_user_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_user_id_key UNIQUE (user_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: users users_username_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_username_key UNIQUE (username);


--
-- Name: idx_categories_user_name; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_categories_user_name ON public.categories USING btree (user_id, category_name);


--
-- Name: idx_chat_history_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_chat_history_created_at ON public.chat_history USING btree (created_at);


--
-- Name: idx_chat_history_session; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_chat_history_session ON public.chat_history USING btree (session_id);


--
-- Name: idx_chat_history_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_chat_history_user_id ON public.chat_history USING btree (user_id);


--
-- Name: idx_notifications_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_user_id ON public.notifications USING btree (user_id);


--
-- Name: idx_transactions_category_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transactions_category_id ON public.transactions USING btree (category_id);


--
-- Name: idx_transactions_date; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transactions_date ON public.transactions USING btree (transaction_date);


--
-- Name: idx_transactions_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transactions_user_id ON public.transactions USING btree (user_id);


--
-- Name: accounts accounts_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.accounts
    ADD CONSTRAINT accounts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: categories categories_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.categories
    ADD CONSTRAINT categories_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: chat_history chat_history_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_history
    ADD CONSTRAINT chat_history_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: notifications notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: transactions transactions_account_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_account_id_fkey FOREIGN KEY (account_id) REFERENCES public.accounts(account_id) ON DELETE RESTRICT;


--
-- Name: transactions transactions_category_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_category_id_fkey FOREIGN KEY (category_id) REFERENCES public.categories(category_id) ON DELETE RESTRICT;


--
-- Name: transactions transactions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transactions
    ADD CONSTRAINT transactions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- Name: user_profiles user_profiles_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_profiles
    ADD CONSTRAINT user_profiles_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(user_id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

\unrestrict xyH6C2UTXsqfMaVo82sY2Schq6TlVJuLcNBD4BHkVrvL44vFEk7rFhNZLRqV4Pu

