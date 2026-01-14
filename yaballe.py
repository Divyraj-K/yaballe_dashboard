import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
st.set_page_config(layout="wide")

@st.cache_data
def get_data():
    customers = pd.read_csv("customers.csv")
    customers['connection_type'] = customers['connection_type'].fillna('Unknown')
    subscription = pd.read_csv("subscription_events.csv")
    product_events = pd.read_json("product_events.json")
    return customers, subscription, product_events
customers, subscription, product_events = get_data()

countries = sorted(customers['country'].dropna().unique())
segments = sorted(customers['segment'].dropna().unique())
connection_types = sorted(customers['connection_type'].dropna().unique())
subscription['event_ts'] = pd.to_datetime(subscription['event_ts'])
latest_event1 = (
    subscription.sort_values('event_ts')
      .groupby('customer_id')
      .tail(1))
#st.dataframe(latest_event)



#####---------------Filter view-----------------
country = st.sidebar.multiselect("Select Country",options=["All"]+countries,default=["All"])
if "All" in country:
    selected_countries = countries
else:
    selected_countries = country

segment = st.sidebar.multiselect("Select segment",options=["All"]+segments,default=["All"])
if "All" in segment:
    selected_segments = segments
else:
    selected_segments = segment

connection_type = st.sidebar.multiselect("Select Connection type",options=["All"]+connection_types,default=["All"])
if "All" in connection_type:
    selected_connection_types = connection_types
else:
    selected_connection_types = connection_type

filtered_customers = customers[
    (customers['country'].isin(selected_countries)) &
    (customers['segment'].isin(selected_segments)) &
    (customers['connection_type'].isin(selected_connection_types))]

remaining_customer_ids = filtered_customers['customer_id'].unique().tolist()
cf = customers[customers['customer_id'].isin(remaining_customer_ids)]
subs = subscription[subscription['customer_id'].isin(remaining_customer_ids)]
latest_event = latest_event1[latest_event1['customer_id'].isin(remaining_customer_ids)]

#####-------------------------------------------




trial_users = subs[subs['plan_to'] == 'trial']['customer_id'].nunique()
paid_users = subs[subs['plan_to'].isin(['basic', 'pro'])]['customer_id'].nunique()
cancelled_users = subs[subs['status'] == 'canceled']['customer_id'].nunique()
###### --------------------KPIs--------------------------
col1, col2, col3,col4 = st.columns([1,1,1,1])
col1.metric("Active Paid Users", latest_event[latest_event['status'].isin(['active'])]['customer_id'].nunique())
##----
trial_to_paid_users = subs[(subs['plan_from'] == 'trial') & (subs['plan_to'].isin(['basic', 'pro']))]['customer_id'].nunique()
trial_to_paid_pct = round((trial_to_paid_users / trial_users) * 100, 2) if trial_users else 0
col2.metric("Trial → Paid %", f"{trial_to_paid_pct}%")
##----
paid_to_cancel = subs[(subs['plan_from'].isin(['basic', 'pro'])) & (subs['status'] == 'canceled')]['customer_id'].nunique()
churn_pct = round((paid_to_cancel / paid_users) * 100, 2) if paid_users else 0
col3.metric("Paid Churn %", f"{churn_pct}%")
##----
col4.metric("Total Revenue USD", int(subs['price_usd'].sum()))
#-------------------------------------------------------------------------------------

####
#subs['month'] = subs['event_ts'].dt.to_period('M').astype(str)
subs['event_ts'] = pd.to_datetime(
    subs['event_ts'],
    errors='coerce',
    utc=True
)


#---------------------Month wise Revenue --------------
revenue_df = subs[subs['plan_to'].isin(['basic', 'pro'])]
monthly_revenue = (revenue_df.groupby(['month', 'plan_to'], as_index=False).agg(total_revenue=('price_usd', 'sum')))

fig = px.bar(monthly_revenue,x='month',y='total_revenue',color='plan_to',title='Monthly Revenue by Plan (Basic vs Pro)',
    labels={'month': 'Month','total_revenue': 'Revenue (USD)','plan_to': 'Plan Type'},barmode='stack',text_auto=True)

fig.update_layout(xaxis_tickangle=-45,legend_title_text='Plan',hovermode='x unified')

st.plotly_chart(fig, use_container_width=True)
#-------------------------------------------------------------------------------------



#-------------------------------------------------------------------------------------
cf['signup_date'] = pd.to_datetime(cf['signup_date'],format='%d-%m-%Y')

cf['signup_month'] = cf['signup_date'].dt.to_period('M').astype(str)
#cf2 = cf[cf['segment'].isin(['New'])]
monthly_signups = (
    cf.groupby('signup_month')['customer_id'].nunique().reset_index(name='new_customers').sort_values('signup_month'))

fig = px.area(
    monthly_signups,
    x='signup_month',
    y='new_customers',
    markers=True,
    title='Month-wise New Customer Signups'
)

fig.update_layout(
    xaxis_title='Signup Month',
    yaxis_title='Number of New Customers',
    hovermode='x unified'
)

st.plotly_chart(fig, use_container_width=True)
#-------------------------------------------------------------------------------------




#conversion_rate = round((paid_users / trial_users) * 100, 2) if trial_users > 0 else 0
#
#monthly = (subs.groupby(['month', 'status']).size().reset_index(name='count'))
#
#fig_trend = px.line(
#    monthly,
#    x='month',
#    y='count',
#    color='status',
#    markers=True,
#    title='Monthly Subscription Events'
#)
#
c1,c2,c3 = st.columns([1,1,1])
#c1.plotly_chart(fig_trend, use_container_width=True)


plan_dist = (latest_event.groupby('plan_to').size().reset_index(name='count'))
plan_dist['percentage'] = round((plan_dist['count'] / plan_dist['count'].sum()) * 100, 2)

ac_cf = cf[cf['number_of_stores']>0]
connetion_type_dist = (ac_cf.groupby('connection_type').size().reset_index(name='count'))
connetion_type_dist['percentage'] = round((connetion_type_dist['count'] / connetion_type_dist['count'].sum()) * 100, 2)

segment_dist = (ac_cf.groupby('segment').size().reset_index(name='count'))
segment_dist['percentage'] = round((segment_dist['count'] / segment_dist['count'].sum()) * 100, 2)


fig1 = px.pie(plan_dist,names='plan_to',values='count',hole=0.5,title='Current Customer Distribution by Plan')

fig1.update_traces(textinfo='percent+label',hovertemplate='<b>%{label}</b><br>Customers: %{value}<br>Percentage: %{percent}')

c1.plotly_chart(fig1, use_container_width=True)

fig2 = px.pie(connetion_type_dist,names='connection_type',values='count',hole=0.5,title='Current Customer Distribution by Connection Type')

fig2.update_traces(textinfo='percent+label',hovertemplate='<b>%{label}</b><br>Customers: %{value}<br>Percentage: %{percent}')

c2.plotly_chart(fig2, use_container_width=True)

fig3 = px.pie(segment_dist,names='segment',values='count',hole=0.5,title='Current Customer Distribution by Segment')

fig3.update_traces(textinfo='percent+label',hovertemplate='<b>%{label}</b><br>Customers: %{value}<br>Percentage: %{percent}')

c3.plotly_chart(fig3, use_container_width=True)
###-------------------------------
churn_df = cf
churn_df['is_churn'] = np.where(churn_df['number_of_stores']>0,1,0)
country_churn = (churn_df.groupby('country').agg(total_customers=('customer_id', 'nunique'),churned_customers=('is_churn', 'sum')).reset_index())

country_churn['churn_pct'] = (country_churn['churned_customers'] / country_churn['total_customers'] * 100)
fig4 = px.bar(country_churn.sort_values('churn_pct', ascending=False),x='country',y='churn_pct',text_auto='.1f',title='Country-wise Churn Rate (%)')

fig4.update_layout(yaxis_title='Churn Rate (%)',xaxis_title='Country')

st.plotly_chart(fig4, use_container_width=True)




