def max_product(list_a, list_b):
    output = {}
    for i, a in enumerate(list_a):
        for j, b in enumerate(list_b):
            value = output.get(i + j)
            if value is not None:
                if value[0] == a + b:
                    value[1].append((i, j))
                    continue
                elif value[0] > a + b:
                    continue
            output[i + j] = (a + b, [(i, j)])
    return {k: output[k] for k in sorted(output)}


def max_level(n, curves):
    bc_product = max_product(*curves[1:3])
    de_product = max_product(*curves[3:5])
    for t, (t_max, t_values) in bc_product.items():
        if t > n:
            break
        for u, (u_max, u_values) in de_product.items():
            a = n - (t + u)
            if a < 0:
                break
            a_m = curves[0].get(a)
            if a_m is not None:
                yield t_max + u_max + a_m, a, t_values, u_values


def max_levels(levels, curves):
    for n in range(levels + 1):
        total, a, bc, de = max(max_level(n, curves), key=lambda i: i[0])
        yield total, [
            (a, b, c, d, e)
            for b, c in bc
            for d, e in de
        ]
