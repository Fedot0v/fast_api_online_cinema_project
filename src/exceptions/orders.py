class OrderNotFoundError(Exception):
    """Exception raised for order not found."""
    def __init__(self, order_id: int):
        self.order_id = order_id
        super().__init__(f"Order with id {order_id} not found")
