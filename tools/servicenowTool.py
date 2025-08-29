import os
import requests
from typing import Dict, Any, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()

SN_INSTANCE_URL = os.getenv("SERVICENOW_INSTANCE_URL")
SN_USERNAME = os.getenv("SERVICENOW_USERNAME")
SN_PASSWORD = os.getenv("SERVICENOW_PASSWORD")

DEFAULT_LIMIT = 50

class ServiceNowClient:
    def __init__(self,
                 base_url: Optional[str] = None,
                 username: Optional[str] = None,
                 password: Optional[str] = None) -> None:
        self.base_url = (base_url or SN_INSTANCE_URL or "").rstrip("/")
        self.username = username or SN_USERNAME
        self.password = password or SN_PASSWORD
        if not self.base_url or not self.username or not self.password:
            raise ValueError("Missing ServiceNow configuration: SN_INSTANCE_URL, SN_USERNAME, SN_PASSWORD")

    def _request(self, method: str, path: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        response = requests.request(
            method=method,
            url=url,
            auth=(self.username, self.password),
            headers={"Accept": "application/json"},
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        return data

    def _request_json(self, method: str, path: str, json_body: Dict[str, Any]) -> Dict[str, Any]:
        url = f"{self.base_url}{path}"
        response = requests.request(
            method=method,
            url=url,
            auth=(self.username, self.password),
            headers={"Accept": "application/json", "Content-Type": "application/json"},
            json=json_body,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    # Minimal group listing used by groups-with-users-tasks
    def list_groups(self, query: Optional[str] = None, limit: int = DEFAULT_LIMIT, offset: int = 0) -> List[Dict[str, Any]]:
        params: Dict[str, Any] = {
            "sysparm_limit": str(limit),
            "sysparm_offset": str(offset),
            "sysparm_fields": "sys_id,name,description,active,email"
        }
        if query:
            params["sysparm_query"] = query
        data = self._request("GET", "/api/now/table/sys_user_group", params)
        return data.get("result", [])

    def list_all_groups(self, query: Optional[str] = None, page_size: int = DEFAULT_LIMIT, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        offset = 0
        pages = 0
        while True:
            page = self.list_groups(query=query, limit=page_size, offset=offset)
            if not page:
                break
            results.extend(page)
            offset += len(page)
            pages += 1
            if len(page) < page_size:
                break
            if max_pages is not None and pages >= max_pages:
                break
        return results

    def list_group_members(self, group_sys_id: str, limit: int = DEFAULT_LIMIT, offset: int = 0) -> List[Dict[str, Any]]:
        """Return users that belong to a given group via sys_user_grmember.
        Dot-walked fields are returned as flat keys (e.g., 'user.name').
        """
        params: Dict[str, Any] = {
            "sysparm_limit": str(limit),
            "sysparm_offset": str(offset),
            "sysparm_fields": "user,user.sys_id,user.name,user.user_name,user.email,user.active",
            "sysparm_query": f"group={group_sys_id}",
            "sysparm_display_value": "true",
        }
        data = self._request("GET", "/api/now/table/sys_user_grmember", params)
        rows = data.get("result", [])
        users: List[Dict[str, Any]] = []
        for row in rows:
            users.append({
                "sys_id": row.get("user.sys_id") or row.get("user"),
                "name": row.get("user.name"),
                "user_name": row.get("user.user_name"),
                "email": row.get("user.email"),
                "active": row.get("user.active"),
            })
        return users

    def list_all_group_members(self, group_sys_id: str, page_size: int = DEFAULT_LIMIT, max_pages: Optional[int] = None) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        offset = 0
        pages = 0
        while True:
            page = self.list_group_members(group_sys_id=group_sys_id, limit=page_size, offset=offset)
            if not page:
                break
            results.extend(page)
            offset += len(page)
            pages += 1
            if len(page) < page_size:
                break
            if max_pages is not None and pages >= max_pages:
                break
        return results

    # NOTE: Standalone groups-with-users was pruned; consolidated into with-users-and-tasks below

    # ---- Tasks assigned to user ----
    def list_user_tasks(
        self,
        user_sys_id: str,
        table: str = "task",
        limit: int = DEFAULT_LIMIT,
        offset: int = 0,
        fields: Optional[str] = None,
        additional_query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not fields:
            fields = "sys_id,number,short_description,state,priority,sys_class_name,opened_at,sys_updated_on"
        query_parts: List[str] = [f"assigned_to={user_sys_id}"]
        if additional_query:
            query_parts.append(additional_query)
        params: Dict[str, Any] = {
            "sysparm_limit": str(limit),
            "sysparm_offset": str(offset),
            "sysparm_fields": fields,
            "sysparm_query": "^".join(query_parts),
        }
        data = self._request("GET", f"/api/now/table/{table}", params)
        return data.get("result", [])

    def list_all_user_tasks(
        self,
        user_sys_id: str,
        table: str = "task",
        page_size: int = DEFAULT_LIMIT,
        max_pages: Optional[int] = None,
        fields: Optional[str] = None,
        additional_query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        offset = 0
        pages = 0
        while True:
            page = self.list_user_tasks(
                user_sys_id=user_sys_id,
                table=table,
                limit=page_size,
                offset=offset,
                fields=fields,
                additional_query=additional_query,
            )
            if not page:
                break
            results.extend(page)
            offset += len(page)
            pages += 1
            if len(page) < page_size:
                break
            if max_pages is not None and pages >= max_pages:
                break
        return results

    def list_groups_with_users_and_tasks(
        self,
        group_query: Optional[str] = None,
        group_page_size: int = DEFAULT_LIMIT,
        group_max_pages: Optional[int] = None,
        member_page_size: int = DEFAULT_LIMIT,
        member_max_pages: Optional[int] = None,
        task_table: str = "task",
        task_page_size: int = DEFAULT_LIMIT,
        task_max_pages: Optional[int] = None,
        task_fields: Optional[str] = None,
        task_additional_query: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        groups = self.list_all_groups(query=group_query, page_size=group_page_size, max_pages=group_max_pages)
        enriched: List[Dict[str, Any]] = []
        for g in groups:
            group_id = g.get("sys_id")
            members = self.list_all_group_members(group_id, page_size=member_page_size, max_pages=member_max_pages) if group_id else []
            users_with_tasks: List[Dict[str, Any]] = []
            for u in members:
                u_id = u.get("sys_id")
                tasks = self.list_all_user_tasks(
                    user_sys_id=u_id,
                    table=task_table,
                    page_size=task_page_size,
                    max_pages=task_max_pages,
                    fields=task_fields,
                    additional_query=task_additional_query,
                ) if u_id else []
                users_with_tasks.append({**u, "tasks": tasks, "task_count": len(tasks)})
            enriched.append({**g, "users": users_with_tasks, "user_count": len(users_with_tasks)})
        return enriched

# Convenience helpers
_client: Optional[ServiceNowClient] = None

def get_servicenow_client() -> ServiceNowClient:
    global _client
    if _client is None:
        _client = ServiceNowClient()
    return _client


def fetch_groups_with_users_and_tasks(
    group_query: Optional[str] = None,
    group_page_size: int = DEFAULT_LIMIT,
    group_max_pages: Optional[int] = None,
    member_page_size: int = DEFAULT_LIMIT,
    member_max_pages: Optional[int] = None,
    task_table: str = "task",
    task_page_size: int = DEFAULT_LIMIT,
    task_max_pages: Optional[int] = None,
    task_fields: Optional[str] = None,
    task_additional_query: Optional[str] = None,
) -> List[Dict[str, Any]]:
    return get_servicenow_client().list_groups_with_users_and_tasks(
        group_query=group_query,
        group_page_size=group_page_size,
        group_max_pages=group_max_pages,
        member_page_size=member_page_size,
        member_max_pages=member_max_pages,
        task_table=task_table,
        task_page_size=task_page_size,
        task_max_pages=task_max_pages,
        task_fields=task_fields,
        task_additional_query=task_additional_query,
    )


# Minimal helpers for incident creation
def find_group(name: str) -> Optional[Dict[str, Any]]:
    client = get_servicenow_client()
    params: Dict[str, Any] = {
        "sysparm_limit": "1",
        "sysparm_fields": "sys_id,name,active,email,description",
        "sysparm_query": f"name={name}",
    }
    data = client._request("GET", "/api/now/table/sys_user_group", params)
    results = data.get("result", [])
    return results[0] if results else None


def create_incident(payload: Dict[str, Any]) -> Dict[str, Any]:
    client = get_servicenow_client()
    data = client._request_json("POST", "/api/now/table/incident", payload)
    return data.get("result", data)


def find_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    client = get_servicenow_client()
    params: Dict[str, Any] = {
        "sysparm_limit": "1",
        "sysparm_fields": "sys_id,name,user_name,email,active",
        "sysparm_query": f"email={email}",
    }
    data = client._request("GET", "/api/now/table/sys_user", params)
    results = data.get("result", [])
    return results[0] if results else None

# NEW: find user by display name (best-effort if email unknown)
def find_user_by_name(name: str) -> Optional[Dict[str, Any]]:
    client = get_servicenow_client()
    params: Dict[str, Any] = {
        "sysparm_limit": "1",
        "sysparm_fields": "sys_id,name,user_name,email,active",
        "sysparm_query": f"name={name}",
    }
    data = client._request("GET", "/api/now/table/sys_user", params)
    results = data.get("result", [])
    return results[0] if results else None

# NEW: choose an assignee for a given group name
def resolve_group_and_assignee(group_name: str) -> Tuple[Optional[str], Optional[str]]:
    """Return (assignment_group_sys_id, assigned_to_sys_id) for given group name.
    Picks first active member if available.
    """
    group = find_group(group_name)
    if not group:
        return None, None
    group_sys_id = group.get("sys_id")
    if not group_sys_id:
        return None, None

    members = get_servicenow_client().list_all_group_members(group_sys_id)
    assigned_to = None
    for m in members:
        if str(m.get("active")).lower() == "true":
            assigned_to = m.get("sys_id")
            break
    return group_sys_id, assigned_to

# NEW: build caller/assignment fields for incident creation
def build_incident_assignment_fields(
    caller_email: Optional[str],
    caller_name: Optional[str],
    group_name: Optional[str],
) -> Dict[str, Any]:
    fields: Dict[str, Any] = {}
    
    import logging
    logger = logging.getLogger(__name__)

    # caller_id resolution
    caller: Optional[Dict[str, Any]] = None
    
    logger.info(f"Attempting to resolve caller: email={caller_email}, name={caller_name}")
    
    # Try email first (most reliable)
    if caller_email:
        logger.info(f"Looking up user by email: {caller_email}")
        caller = find_user_by_email(caller_email)
        if caller:
            logger.info(f"Found user by email: {caller.get('name', 'Unknown')} (sys_id: {caller.get('sys_id', 'None')})")
        else:
            logger.warning(f"No user found by email: {caller_email}")
    
    # Try name if email lookup failed
    if not caller and caller_name:
        logger.info(f"Looking up user by name: {caller_name}")
        caller = find_user_by_name(caller_name)
        if caller:
            logger.info(f"Found user by name: {caller.get('name', 'Unknown')} (sys_id: {caller.get('sys_id', 'None')})")
        else:
            logger.warning(f"No user found by name: {caller_name}")
    
    # Set caller_id if found
    if caller and caller.get("sys_id"):
        fields["caller_id"] = caller["sys_id"]
        logger.info(f"Set caller_id to: {caller['sys_id']}")
    else:
        logger.warning("No caller_id set - user not found in ServiceNow")

    # assignment resolution
    if group_name:
        logger.info(f"Resolving assignment group: {group_name}")
        group_sys_id, assigned_to_sys_id = resolve_group_and_assignee(group_name)
        if group_sys_id:
            fields["assignment_group"] = group_sys_id
            logger.info(f"Set assignment_group to: {group_sys_id}")
        if assigned_to_sys_id:
            fields["assigned_to"] = assigned_to_sys_id
            logger.info(f"Set assigned_to to: {assigned_to_sys_id}")

    logger.info(f"Final assignment fields: {fields}")
    return fields

# ---- Helpers for notification agent ----
def get_incident_by_sys_id(sys_id: str) -> Optional[Dict[str, Any]]:
    client = get_servicenow_client()
    params = {
        "sysparm_limit": "1",
        "sysparm_fields": "number,short_description,description,caller_id,assignment_group,assigned_to,sys_id,category,impact,urgency,priority,contact_type,state"
    }
    data = client._request("GET", f"/api/now/table/incident/{sys_id}", params)
    result = data.get("result")
    return result


def get_latest_incident() -> Optional[Dict[str, Any]]:
    client = get_servicenow_client()
    params = {
        "sysparm_limit": "1",
        "sysparm_fields": "number,short_description,description,caller_id,assignment_group,assigned_to,sys_id,category,impact,urgency,priority,contact_type,state",
        "sysparm_query": "ORDERBYDESCsys_created_on",
    }
    data = client._request("GET", "/api/now/table/incident", params)
    results = data.get("result", [])
    return results[0] if results else None


def get_user_by_sys_id(sys_id: str) -> Optional[Dict[str, Any]]:
    client = get_servicenow_client()
    params = {
        "sysparm_limit": "1",
        "sysparm_fields": "sys_id,name,user_name,email,active",
    }
    data = client._request("GET", f"/api/now/table/sys_user/{sys_id}", params)
    result = data.get("result")
    return result


def get_group_by_sys_id(sys_id: str) -> Optional[Dict[str, Any]]:
    client = get_servicenow_client()
    params = {
        "sysparm_limit": "1",
        "sysparm_fields": "sys_id,name,active,email,description",
    }
    data = client._request("GET", f"/api/now/table/sys_user_group/{sys_id}", params)
    result = data.get("result")
    return result


def get_incident_updated_at(sys_id: str) -> Optional[str]:
    """Return the sys_updated_on timestamp of an incident."""
    client = get_servicenow_client()
    params = {
        "sysparm_fields": "sys_updated_on",
    }
    data = client._request("GET", f"/api/now/table/incident/{sys_id}", params)
    result = data.get("result")
    if not result:
        return None
    return result.get("sys_updated_on")
