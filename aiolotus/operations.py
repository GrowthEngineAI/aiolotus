from aiolotus.schemas import *


class APIOperation:
    # Events
    track_event = BaseOperation(
        url = "/api/track/",
        name = "track_event",
        http_method = HttpMethod.POST,
        api_method = ApiMethod.TRACK,
        api_model = LotusEvent,
    )

    # Customers
    get_all_customers = BaseOperation(
        url = "/api/customers/",
        name = "get_all_customers",
        http_method = HttpMethod.GET,
        api_method = ApiMethod.GET_ALL,
        api_model = LotusCustomer,
    )
    create_customer = BaseOperation(
        url = "/api/customers/",
        name = "create_customer",
        http_method = HttpMethod.POST,
        api_method = ApiMethod.CREATE,
        api_model = LotusCustomer,
    )
    
    get_customer_detail = BaseOperation(
        url = "/api/customer_detail/",
        name = "get_customer_detail",
        http_method = HttpMethod.GET,
        itemized = True,
        api_method = ApiMethod.GET_DETAIL,
        api_model = LotusCustomer,
    )
    
    delete_customer = BaseOperation(
        url = "/api/customers/",
        name = "delete_customer",
        http_method = HttpMethod.DELETE,
        itemized = True,
        api_method = ApiMethod.DELETE,
        api_model = LotusCustomer,
    )

    create_batch_customers = BaseOperation(
        url = "/api/batch_create_customers/",
        name = "create_batch_customers",
        http_method = HttpMethod.POST,
        api_method = ApiMethod.CREATE_BATCH,
        api_model = LotusCustomer,
    )

    # get_customer_access = BaseOperation(
    #     url = "/api/customer_access/",
    #     name = "get_customer_access",
    #     http_method = HttpMethod.GET,
    # )

    # Subscriptions
    get_all_subscriptions = BaseOperation(
        url = "/api/subscriptions/",
        name = "get_all_subscriptions",
        http_method = HttpMethod.GET,
        api_method = ApiMethod.GET_ALL,
        api_model = LotusSubscription,
    )

    create_subscription = BaseOperation(
        url = "/api/subscriptions/",
        name = "create_subscription",
        http_method = HttpMethod.POST,
        api_method = ApiMethod.CREATE,
        api_model = LotusSubscription,
    )

    cancel_subscription = BaseOperation(
        url = "/api/subscriptions/",
        name = "cancel_subscription",
        http_method = HttpMethod.PATCH,
        api_method = ApiMethod.CANCEL,
        api_model = LotusSubscription,
    )

    get_subscription_detail = BaseOperation(
        url = "/api/subscriptions/",
        name = "get_subscription_detail",
        http_method = HttpMethod.GET,
        itemized = True,
        api_method = ApiMethod.GET_DETAIL,
        api_model = LotusSubscription,
    )

    update_subscription = BaseOperation(
        url = "/api/subscriptions/",
        name = "update_subscription",
        http_method = HttpMethod.PATCH,
        api_method = ApiMethod.UPDATE,
        api_model = LotusSubscription,
    )

    change_subscription_plan = BaseOperation(
        url = "/api/subscriptions/",
        name = "change_subscription_plan",
        http_method = HttpMethod.PATCH,
        api_method = ApiMethod.CHANGE,
        api_model = LotusSubscription,
    )

    # Plans
    get_all_plans = BaseOperation(
        url = "/api/plans/",
        name = "get_all_plans",
        http_method = HttpMethod.GET,
        api_method = ApiMethod.GET_ALL,
        api_model = LotusPlan,
    )

    get_plan_detail = BaseOperation(
        url = "/api/plans/",
        name = "get_plan_detail",
        http_method = HttpMethod.GET,
        itemized = True,
        api_method = ApiMethod.GET_DETAIL,
        api_model = LotusPlan,
    )

    update_plan = BaseOperation(
        url = "/api/plans/",
        name = "update_plan",
        http_method = HttpMethod.PATCH,
        itemized = True,
        api_method = ApiMethod.UPDATE,
        api_model = LotusPlan,
    )

    create_plan = BaseOperation(
        url = "/api/plans/",
        name = "create_plan",
        http_method = HttpMethod.POST,
        api_method = ApiMethod.CREATE,
        api_model = LotusPlan,
    )

    # # Plan Versions
    # create_plan_version = BaseOperation(
    #     url = "/api/plan_versions/",
    #     name = "create_plan_version",
    #     http_method = HttpMethod.POST,
    # )

    # update_plan_version = BaseOperation(
    #     url = "/api/plan_versions/",
    #     name = "update_plan_version",
    #     http_method = HttpMethod.PATCH,
    #     itemized = True,
    # )


    # Invoices
    # get_all_invoices = BaseOperation(
    #     url = "/api/invoices/",
    #     name = "get_all_invoices",
    #     http_method = HttpMethod.GET,
    # )
    # get_invoice_detail = BaseOperation(
    #     url = "/api/invoices/",
    #     name = "get_invoice_detail",
    #     http_method = HttpMethod.GET,
    #     itemized = True,
    # )
    # create_invoice = BaseOperation(
    #     url = "/api/invoices/",
    #     name = "create_invoice",
    #     http_method = HttpMethod.POST,
    # )
    # update_invoice = BaseOperation(
    #     url = "/api/invoices/",
    #     name = "update_invoice",
    #     http_method = HttpMethod.PATCH,
    #     itemized = True,
    # )
    # delete_invoice = BaseOperation(
    #     url = "/api/invoices/",
    #     name = "delete_invoice",
    #     http_method = HttpMethod.DELETE,
    # )

    
    # Metrics
    get_all_metrics = BaseOperation(
        url = "/api/metrics/",
        name = "get_metrics",
        http_method = HttpMethod.GET,
        api_method = ApiMethod.GET_ALL,
        api_model = LotusMetric,
    )
    get_metric_detail = BaseOperation(
        url = "/api/metrics/",
        name = "get_metric_detail",
        http_method = HttpMethod.GET,
        itemized = True,
        api_method = ApiMethod.GET_DETAIL,
        api_model = LotusMetric,
    )
    update_metric = BaseOperation(
        url = "/api/metrics/",
        name = "update_metric",
        http_method = HttpMethod.PATCH,
        itemized = True,
        api_method = ApiMethod.UPDATE,
        api_model = LotusMetric,
    )
    create_metric = BaseOperation(
        url = "/api/metrics/",
        name = "create_metric",
        http_method = HttpMethod.POST,
        api_method = ApiMethod.CREATE,
        api_model = LotusMetric,
    )

    # Users
    get_all_users = BaseOperation(
        url = "/api/users/",
        name = "get_all_users",
        http_method = HttpMethod.GET,
        api_model = LotusUser,
        api_method = ApiMethod.GET_ALL,
    )
    get_user_detail = BaseOperation(
        url = "/api/users/",
        name = "get_user_detail",
        http_method = HttpMethod.GET,
        itemized = True,
        api_method = ApiMethod.GET_DETAIL,
        api_model = LotusUser,
    )
    update_user = BaseOperation(
        url = "/api/users/",
        name = "update_user",
        http_method = HttpMethod.PATCH,
        itemized = True,
        api_method = ApiMethod.UPDATE,
        api_model = LotusUser,
    )
    create_user = BaseOperation(
        url = "/api/users/",
        name = "create_user",
        http_method = HttpMethod.POST,
        api_method = ApiMethod.CREATE,
        api_model = LotusUser,
    )
    delete_user = BaseOperation(
        url = "/api/users/",
        name = "delete_user",
        http_method = HttpMethod.DELETE,
        itemized = True,
        api_method = ApiMethod.DELETE,
        api_model = LotusUser,
    )