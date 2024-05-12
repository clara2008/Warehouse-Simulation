-- db tables

-- create table for transport units
CREATE TABLE public.transport_units (
	id varchar NULL,
	color varchar NULL,
	"type" varchar NULL,
	weight int4 NULL,
	height int4 NULL,
	length int4 NULL,
	width int4 NULL,
	current_loc varchar NULL,
	outbound_request bool NULL
);

-- create table for warehouse occupancy
CREATE TABLE public.warehouse (
	y int4 NULL,
	x int4 NULL,
	direction varchar NULL,
	seat_id varchar NULL,
	status varchar NULL
);

-- create table for DoS attacker
CREATE TABLE public.dos_table (
	column1 varchar NULL
);
