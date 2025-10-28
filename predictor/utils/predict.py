import math

def poisson_pmf(k, lamb):
    # simple pmf without external dependencies
    return (lamb**k) * math.exp(-lamb) / math.factorial(k)

def poisson_prob_matrix(lambda_home, lambda_away, max_goals=5):
    matrix = {}
    for i in range(max_goals+1):
        matrix[i] = {}
        for j in range(max_goals+1):
            matrix[i][j] = poisson_pmf(i, lambda_home) * poisson_pmf(j, lambda_away)
    return matrix

def match_probabilities(lambda_home, lambda_away, max_goals=5):
    mat = poisson_prob_matrix(lambda_home, lambda_away, max_goals)
    p_home_win = sum(mat[i][j] for i in mat for j in mat[i] if i > j)
    p_draw = sum(mat[i][j] for i in mat for j in mat[i] if i == j)
    p_away_win = sum(mat[i][j] for i in mat for j in mat[i] if i < j)
    best_score = max(((i,j,mat[i][j]) for i in mat for j in mat[i]), key=lambda x: x[2])
    return {
        'home_win': p_home_win,
        'draw': p_draw,
        'away_win': p_away_win,
        'most_likely_score': (best_score[0], best_score[1]),
    }
