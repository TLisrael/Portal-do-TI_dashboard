SELECT 
    c.Status as StatusNumerico,
    CASE 
        WHEN c.Status = 1 THEN 'Em Estoque'
        WHEN c.Status = 2 THEN 'Acesso Remoto'
        WHEN c.Status = 3 THEN 'Em Uso'
        WHEN c.Status = 4 THEN 'Extraviado'
        WHEN c.Status = 5 THEN 'Reparo'
        WHEN c.Status = 6 THEN 'Roubado'
        WHEN c.Status = 7 THEN 'Devolvido'
        WHEN c.Status = 8 THEN 'Descartado'
        WHEN c.Status = 9 THEN 'Danificado'
        ELSE 'Status Indefinido'
    END as Status,
    COUNT(*) as Quantidade
FROM Computadores c
WHERE c.Status IS NOT NULL
GROUP BY c.Status
ORDER BY c.Status