def get_gradient_color(x, max_x, start_color, end_color):
    """
    calculates colors in color gradient
    """
    t = x / max_x
    return (
        # rgb-werte interpolieren
        int(start_color[0] + t * (end_color[0] - start_color[0])),
        int(start_color[1] + t * (end_color[1] - start_color[1])),
        int(start_color[2] + t * (end_color[2] - start_color[2])) 
    )
