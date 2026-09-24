"""Юнит-тесты сущности PaginatedResult: вычисление числа страниц."""

import pytest

from src.domain.entities.pagination import PaginatedResult


class TestPaginatedResult:
    """Группа тестов пагинации."""

    @pytest.mark.parametrize(
        "total, page_size, expected_pages",
        [
            (0, 10, 0),
            (1, 10, 1),
            (10, 10, 1),
            (11, 10, 2),
            (25, 10, 3),
        ],
        ids=["empty", "one-item", "exact-page", "overflow", "three-pages"],
    )
    def test_pages_calculation(self, total: int, page_size: int, expected_pages: int) -> None:
        """
        Тестируем: вычисление количества страниц.
        Отдаём: комбинации total/page_size от пустой выборки до переполнения.
        Ожидаем: pages соответствует округлению вверх от деления.
        """
        result = PaginatedResult(items=[], total=total, page=1, page_size=page_size)

        assert result.pages == expected_pages
