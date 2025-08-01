# 新功能开发模板

本模板提供了在 Flask API Template 中添加新功能的标准化流程和代码模板。

## 📋 开发清单

### 1. 规划阶段
- [ ] 定义功能需求和用例
- [ ] 设计数据模型和 API 接口
- [ ] 确定权限和安全要求
- [ ] 评估对现有功能的影响

### 2. 数据层
- [ ] 创建数据模型 (`app/models/`)
- [ ] 创建数据库迁移
- [ ] 编写模型单元测试

### 3. 业务层
- [ ] 创建服务类 (`app/services/`)
- [ ] 实现业务逻辑
- [ ] 编写服务层单元测试

### 4. 控制层
- [ ] 创建控制器 (`app/controllers/`)
- [ ] 实现 API 端点
- [ ] 添加输入验证和错误处理

### 5. API 文档
- [ ] 创建 API 命名空间 (`app/api/`)
- [ ] 定义请求/响应模型
- [ ] 添加 Swagger 文档注解

### 6. 数据验证
- [ ] 创建数据模式 (`app/schemas/`)
- [ ] 实现输入验证
- [ ] 添加自定义验证规则

### 7. 测试
- [ ] 编写集成测试
- [ ] 编写 API 端点测试
- [ ] 验证错误处理

### 8. 文档
- [ ] 更新 API 文档
- [ ] 添加使用示例
- [ ] 更新 README

## 🏗️ 代码模板

### 数据模型模板

```python
# app/models/your_model.py
"""
Your Model - 数据模型

描述你的模型的用途和功能。
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import BaseModel


class YourModel(BaseModel):
    """你的模型类"""

    __tablename__ = 'your_table'

    # 基础字段
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)

    # 外键关系（如果需要）
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship("User", back_populates="your_models")

    # 索引
    __table_args__ = (
        # 添加复合索引
        # Index('ix_your_table_user_name', 'user_id', 'name'),
    )

    def __repr__(self):
        return f'<YourModel {self.name}>'

    def to_dict(self):
        """转换为字典"""
        data = super().to_dict()
        data.update({
            'name': self.name,
            'description': self.description,
            'is_active': self.is_active,
            'user_id': self.user_id
        })
        return data

    @classmethod
    def create(cls, **kwargs):
        """创建新实例"""
        instance = cls(**kwargs)
        instance.save()
        return instance

    def update(self, **kwargs):
        """更新实例"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()
        return self
```

### 服务层模板

```python
# app/services/your_service.py
"""
Your Service - 业务逻辑层

处理与你的功能相关的业务逻辑。
"""

from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from app.extensions import db
from app.models.your_model import YourModel
from app.utils.exceptions import ValidationError, NotFoundError, ConflictError


class YourService:
    """你的服务类"""

    @staticmethod
    def create_item(data: Dict[str, Any], user_id: int) -> YourModel:
        """创建新项目"""
        # 验证数据
        YourService._validate_create_data(data)

        # 检查重复
        existing = YourModel.query.filter_by(
            name=data['name'],
            user_id=user_id
        ).first()

        if existing:
            raise ConflictError(f"Item with name '{data['name']}' already exists")

        # 创建新项目
        item = YourModel.create(
            name=data['name'],
            description=data.get('description'),
            user_id=user_id
        )

        return item

    @staticmethod
    def get_item(item_id: int, user_id: Optional[int] = None) -> YourModel:
        """获取项目详情"""
        query = YourModel.query.filter_by(id=item_id)

        if user_id:
            query = query.filter_by(user_id=user_id)

        item = query.first()
        if not item:
            raise NotFoundError("Item not found")

        return item

    @staticmethod
    def get_items(user_id: Optional[int] = None,
                  page: int = 1,
                  per_page: int = 20,
                  search: Optional[str] = None,
                  is_active: Optional[bool] = None) -> Dict[str, Any]:
        """获取项目列表"""
        query = YourModel.query

        # 用户过滤
        if user_id:
            query = query.filter_by(user_id=user_id)

        # 状态过滤
        if is_active is not None:
            query = query.filter_by(is_active=is_active)

        # 搜索过滤
        if search:
            query = query.filter(
                or_(
                    YourModel.name.ilike(f'%{search}%'),
                    YourModel.description.ilike(f'%{search}%')
                )
            )

        # 排序
        query = query.order_by(YourModel.created_at.desc())

        # 分页
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )

        return {
            'items': pagination.items,
            'pagination': {
                'page': pagination.page,
                'per_page': pagination.per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_prev': pagination.has_prev,
                'has_next': pagination.has_next,
                'prev_num': pagination.prev_num,
                'next_num': pagination.next_num
            }
        }

    @staticmethod
    def update_item(item_id: int, data: Dict[str, Any],
                   user_id: Optional[int] = None) -> YourModel:
        """更新项目"""
        item = YourService.get_item(item_id, user_id)

        # 验证更新数据
        YourService._validate_update_data(data)

        # 检查名称重复（如果更新了名称）
        if 'name' in data and data['name'] != item.name:
            existing = YourModel.query.filter(
                and_(
                    YourModel.name == data['name'],
                    YourModel.user_id == item.user_id,
                    YourModel.id != item_id
                )
            ).first()

            if existing:
                raise ConflictError(f"Item with name '{data['name']}' already exists")

        # 更新项目
        item.update(**data)
        return item

    @staticmethod
    def delete_item(item_id: int, user_id: Optional[int] = None,
                   hard_delete: bool = False) -> bool:
        """删除项目"""
        item = YourService.get_item(item_id, user_id)

        if hard_delete:
            # 硬删除
            db.session.delete(item)
            db.session.commit()
        else:
            # 软删除
            item.update(is_active=False)

        return True

    @staticmethod
    def _validate_create_data(data: Dict[str, Any]) -> None:
        """验证创建数据"""
        required_fields = ['name']

        for field in required_fields:
            if field not in data or not data[field]:
                raise ValidationError(f"Field '{field}' is required")

        # 名称长度验证
        if len(data['name']) > 100:
            raise ValidationError("Name must be less than 100 characters")

        # 描述长度验证
        if 'description' in data and data['description'] and len(data['description']) > 1000:
            raise ValidationError("Description must be less than 1000 characters")

    @staticmethod
    def _validate_update_data(data: Dict[str, Any]) -> None:
        """验证更新数据"""
        # 名称长度验证
        if 'name' in data and data['name'] and len(data['name']) > 100:
            raise ValidationError("Name must be less than 100 characters")

        # 描述长度验证
        if 'description' in data and data['description'] and len(data['description']) > 1000:
            raise ValidationError("Description must be less than 1000 characters")
```

### 控制器模板

```python
# app/controllers/your_controller.py
"""
Your Controller - 控制器层

处理 HTTP 请求和响应。
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_current_user

from app.services.your_service import YourService
from app.schemas.your_schemas import YourCreateSchema, YourUpdateSchema
from app.utils.error_handlers import handle_api_error
from app.utils.validation import validate_json


# 创建蓝图
your_bp = Blueprint('your', __name__)


@your_bp.route('/your-items', methods=['POST'])
@jwt_required()
@validate_json(YourCreateSchema)
def create_item():
    """创建新项目"""
    try:
        current_user = get_current_user()
        data = request.get_json()

        item = YourService.create_item(data, current_user.id)

        return jsonify({
            'success': True,
            'message': 'Item created successfully',
            'data': {
                'item': item.to_dict()
            }
        }), 201

    except Exception as e:
        return handle_api_error(e)


@your_bp.route('/your-items', methods=['GET'])
@jwt_required()
def get_items():
    """获取项目列表"""
    try:
        current_user = get_current_user()

        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search')
        is_active = request.args.get('is_active', type=bool)

        # 权限检查：普通用户只能看自己的项目
        user_id = current_user.id if not current_user.is_admin else None

        result = YourService.get_items(
            user_id=user_id,
            page=page,
            per_page=per_page,
            search=search,
            is_active=is_active
        )

        return jsonify({
            'success': True,
            'message': 'Items retrieved successfully',
            'data': {
                'items': [item.to_dict() for item in result['items']],
                'pagination': result['pagination']
            }
        })

    except Exception as e:
        return handle_api_error(e)


@your_bp.route('/your-items/<int:item_id>', methods=['GET'])
@jwt_required()
def get_item(item_id):
    """获取项目详情"""
    try:
        current_user = get_current_user()

        # 权限检查：普通用户只能看自己的项目
        user_id = current_user.id if not current_user.is_admin else None

        item = YourService.get_item(item_id, user_id)

        return jsonify({
            'success': True,
            'message': 'Item retrieved successfully',
            'data': {
                'item': item.to_dict()
            }
        })

    except Exception as e:
        return handle_api_error(e)


@your_bp.route('/your-items/<int:item_id>', methods=['PUT'])
@jwt_required()
@validate_json(YourUpdateSchema)
def update_item(item_id):
    """更新项目"""
    try:
        current_user = get_current_user()
        data = request.get_json()

        # 权限检查：普通用户只能更新自己的项目
        user_id = current_user.id if not current_user.is_admin else None

        item = YourService.update_item(item_id, data, user_id)

        return jsonify({
            'success': True,
            'message': 'Item updated successfully',
            'data': {
                'item': item.to_dict()
            }
        })

    except Exception as e:
        return handle_api_error(e)


@your_bp.route('/your-items/<int:item_id>', methods=['DELETE'])
@jwt_required()
def delete_item(item_id):
    """删除项目"""
    try:
        current_user = get_current_user()

        # 获取查询参数
        hard_delete = request.args.get('hard_delete', False, type=bool)

        # 权限检查：普通用户只能删除自己的项目
        user_id = current_user.id if not current_user.is_admin else None

        YourService.delete_item(item_id, user_id, hard_delete)

        return jsonify({
            'success': True,
            'message': 'Item deleted successfully'
        })

    except Exception as e:
        return handle_api_error(e)
```

### API 文档模板

```python
# app/api/your_namespace.py
"""
Your API Namespace - API 文档定义

定义你的功能的 API 文档。
"""

from flask_restx import Namespace, Resource, fields
from flask_jwt_extended import jwt_required

from app.api.models import error_model, success_model, validation_error_model


# 创建命名空间
your_ns = Namespace('your-items', description='Your items operations', path='/your-items')


# 定义数据模型
your_item_model = your_ns.model('YourItem', {
    'id': fields.Integer(required=True, description='Item ID'),
    'name': fields.String(required=True, description='Item name'),
    'description': fields.String(description='Item description'),
    'is_active': fields.Boolean(description='Whether the item is active'),
    'user_id': fields.Integer(description='Owner user ID'),
    'created_at': fields.DateTime(description='Creation timestamp'),
    'updated_at': fields.DateTime(description='Last update timestamp')
})

your_item_create_model = your_ns.model('YourItemCreate', {
    'name': fields.String(required=True, description='Item name', max_length=100),
    'description': fields.String(description='Item description', max_length=1000)
})

your_item_update_model = your_ns.model('YourItemUpdate', {
    'name': fields.String(description='Item name', max_length=100),
    'description': fields.String(description='Item description', max_length=1000),
    'is_active': fields.Boolean(description='Whether the item is active')
})

your_item_response_model = your_ns.model('YourItemResponse', {
    'success': fields.Boolean(required=True),
    'message': fields.String(required=True),
    'data': fields.Nested(your_ns.model('YourItemData', {
        'item': fields.Nested(your_item_model)
    }))
})

your_items_response_model = your_ns.model('YourItemsResponse', {
    'success': fields.Boolean(required=True),
    'message': fields.String(required=True),
    'data': fields.Nested(your_ns.model('YourItemsData', {
        'items': fields.List(fields.Nested(your_item_model)),
        'pagination': fields.Nested(your_ns.model('Pagination', {
            'page': fields.Integer(),
            'per_page': fields.Integer(),
            'total': fields.Integer(),
            'pages': fields.Integer(),
            'has_prev': fields.Boolean(),
            'has_next': fields.Boolean(),
            'prev_num': fields.Integer(),
            'next_num': fields.Integer()
        }))
    }))
})


@your_ns.route('')
class YourItemListResource(Resource):
    @your_ns.doc('get_your_items', security='Bearer')
    @your_ns.param('page', 'Page number', type='integer', default=1)
    @your_ns.param('per_page', 'Items per page (max 100)', type='integer', default=20)
    @your_ns.param('search', 'Search term', type='string')
    @your_ns.param('is_active', 'Filter by active status', type='boolean')
    @your_ns.marshal_with(your_items_response_model, code=200, description='Items retrieved successfully')
    @your_ns.response(400, 'Invalid query parameters', validation_error_model)
    @your_ns.response(401, 'Invalid or expired access token', error_model)
    @your_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def get(self):
        """
        Get paginated list of your items

        Retrieve a paginated list of items with optional filtering.
        Regular users can only see their own items, admins can see all items.
        """
        pass

    @your_ns.doc('create_your_item', security='Bearer')
    @your_ns.expect(your_item_create_model, validate=True)
    @your_ns.marshal_with(your_item_response_model, code=201, description='Item created successfully')
    @your_ns.response(400, 'Invalid request data', validation_error_model)
    @your_ns.response(401, 'Invalid or expired access token', error_model)
    @your_ns.response(409, 'Item with same name already exists', error_model)
    @your_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def post(self):
        """
        Create a new item

        Create a new item for the current user.
        Item names must be unique per user.
        """
        pass


@your_ns.route('/<int:item_id>')
@your_ns.param('item_id', 'Item ID')
class YourItemResource(Resource):
    @your_ns.doc('get_your_item', security='Bearer')
    @your_ns.marshal_with(your_item_response_model, code=200, description='Item retrieved successfully')
    @your_ns.response(401, 'Invalid or expired access token', error_model)
    @your_ns.response(403, 'Insufficient permissions', error_model)
    @your_ns.response(404, 'Item not found', error_model)
    @your_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def get(self, item_id):
        """
        Get item by ID

        Retrieve item information by ID.
        Users can only access their own items, admins can access any item.
        """
        pass

    @your_ns.doc('update_your_item', security='Bearer')
    @your_ns.expect(your_item_update_model, validate=True)
    @your_ns.marshal_with(your_item_response_model, code=200, description='Item updated successfully')
    @your_ns.response(400, 'Invalid request data', validation_error_model)
    @your_ns.response(401, 'Invalid or expired access token', error_model)
    @your_ns.response(403, 'Insufficient permissions', error_model)
    @your_ns.response(404, 'Item not found', error_model)
    @your_ns.response(409, 'Item with same name already exists', error_model)
    @your_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def put(self, item_id):
        """
        Update item information

        Update item information by ID.
        Users can only update their own items, admins can update any item.
        """
        pass

    @your_ns.doc('delete_your_item', security='Bearer')
    @your_ns.param('hard_delete', 'Whether to permanently delete', type='boolean', default=False)
    @your_ns.marshal_with(success_model, code=200, description='Item deleted successfully')
    @your_ns.response(401, 'Invalid or expired access token', error_model)
    @your_ns.response(403, 'Insufficient permissions', error_model)
    @your_ns.response(404, 'Item not found', error_model)
    @your_ns.response(500, 'Internal server error', error_model)
    @jwt_required()
    def delete(self, item_id):
        """
        Delete item

        Delete item by ID.
        By default performs soft delete (deactivates item).
        Use hard_delete=true for permanent deletion.
        Users can only delete their own items, admins can delete any item.
        """
        pass
```

### 数据验证模式模板

```python
# app/schemas/your_schemas.py
"""
Your Schemas - 数据验证模式

定义你的功能的数据验证规则。
"""

from marshmallow import Schema, fields, validate, validates, ValidationError


class YourCreateSchema(Schema):
    """创建项目的数据验证模式"""

    name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=100, error="Name must be between 1 and 100 characters"),
            validate.Regexp(
                r'^[a-zA-Z0-9\s\-_]+$',
                error="Name can only contain letters, numbers, spaces, hyphens and underscores"
            )
        ]
    )

    description = fields.Str(
        validate=validate.Length(max=1000, error="Description must be less than 1000 characters"),
        allow_none=True
    )

    @validates('name')
    def validate_name(self, value):
        """验证名称"""
        if not value or not value.strip():
            raise ValidationError("Name cannot be empty")

        # 检查是否包含禁用词汇
        forbidden_words = ['admin', 'system', 'root']
        if any(word in value.lower() for word in forbidden_words):
            raise ValidationError("Name contains forbidden words")


class YourUpdateSchema(Schema):
    """更新项目的数据验证模式"""

    name = fields.Str(
        validate=[
            validate.Length(min=1, max=100, error="Name must be between 1 and 100 characters"),
            validate.Regexp(
                r'^[a-zA-Z0-9\s\-_]+$',
                error="Name can only contain letters, numbers, spaces, hyphens and underscores"
            )
        ]
    )

    description = fields.Str(
        validate=validate.Length(max=1000, error="Description must be less than 1000 characters"),
        allow_none=True
    )

    is_active = fields.Bool()

    @validates('name')
    def validate_name(self, value):
        """验证名称"""
        if value is not None and (not value or not value.strip()):
            raise ValidationError("Name cannot be empty")

        # 检查是否包含禁用词汇
        if value:
            forbidden_words = ['admin', 'system', 'root']
            if any(word in value.lower() for word in forbidden_words):
                raise ValidationError("Name contains forbidden words")


class YourQuerySchema(Schema):
    """查询参数的数据验证模式"""

    page = fields.Int(
        validate=validate.Range(min=1, error="Page must be greater than 0"),
        missing=1
    )

    per_page = fields.Int(
        validate=validate.Range(min=1, max=100, error="Per page must be between 1 and 100"),
        missing=20
    )

    search = fields.Str(
        validate=validate.Length(min=2, max=100, error="Search term must be between 2 and 100 characters")
    )

    is_active = fields.Bool()
```

### 测试模板

```python
# tests/unit/test_your_service.py
"""
Your Service 单元测试
"""

import pytest
from unittest.mock import Mock, patch

from app.services.your_service import YourService
from app.models.your_model import YourModel
from app.utils.exceptions import ValidationError, NotFoundError, ConflictError


class TestYourService:
    """YourService 测试类"""

    def test_create_item_success(self, db_session):
        """测试成功创建项目"""
        data = {
            'name': 'Test Item',
            'description': 'Test Description'
        }
        user_id = 1

        with patch.object(YourModel, 'query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = None

            with patch.object(YourModel, 'create') as mock_create:
                mock_item = Mock()
                mock_item.id = 1
                mock_item.name = data['name']
                mock_create.return_value = mock_item

                result = YourService.create_item(data, user_id)

                assert result == mock_item
                mock_create.assert_called_once()

    def test_create_item_duplicate_name(self, db_session):
        """测试创建重复名称的项目"""
        data = {
            'name': 'Existing Item',
            'description': 'Test Description'
        }
        user_id = 1

        with patch.object(YourModel, 'query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = Mock()

            with pytest.raises(ConflictError):
                YourService.create_item(data, user_id)

    def test_create_item_validation_error(self, db_session):
        """测试创建项目时的验证错误"""
        data = {}  # 缺少必需字段
        user_id = 1

        with pytest.raises(ValidationError):
            YourService.create_item(data, user_id)

    def test_get_item_success(self, db_session):
        """测试成功获取项目"""
        item_id = 1
        user_id = 1

        with patch.object(YourModel, 'query') as mock_query:
            mock_item = Mock()
            mock_query.filter_by.return_value.first.return_value = mock_item

            result = YourService.get_item(item_id, user_id)

            assert result == mock_item

    def test_get_item_not_found(self, db_session):
        """测试获取不存在的项目"""
        item_id = 999
        user_id = 1

        with patch.object(YourModel, 'query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = None

            with pytest.raises(NotFoundError):
                YourService.get_item(item_id, user_id)

    def test_get_items_with_pagination(self, db_session):
        """测试获取项目列表（分页）"""
        user_id = 1
        page = 1
        per_page = 10

        with patch.object(YourModel, 'query') as mock_query:
            mock_pagination = Mock()
            mock_pagination.items = [Mock(), Mock()]
            mock_pagination.page = page
            mock_pagination.per_page = per_page
            mock_pagination.total = 2
            mock_pagination.pages = 1
            mock_pagination.has_prev = False
            mock_pagination.has_next = False
            mock_pagination.prev_num = None
            mock_pagination.next_num = None

            mock_query.filter_by.return_value.order_by.return_value.paginate.return_value = mock_pagination

            result = YourService.get_items(user_id=user_id, page=page, per_page=per_page)

            assert 'items' in result
            assert 'pagination' in result
            assert len(result['items']) == 2

    def test_update_item_success(self, db_session):
        """测试成功更新项目"""
        item_id = 1
        user_id = 1
        data = {'name': 'Updated Name'}

        mock_item = Mock()
        mock_item.id = item_id
        mock_item.name = 'Original Name'
        mock_item.user_id = user_id

        with patch.object(YourService, 'get_item', return_value=mock_item):
            with patch.object(YourModel, 'query') as mock_query:
                mock_query.filter.return_value.first.return_value = None

                result = YourService.update_item(item_id, data, user_id)

                assert result == mock_item
                mock_item.update.assert_called_once_with(**data)

    def test_delete_item_soft_delete(self, db_session):
        """测试软删除项目"""
        item_id = 1
        user_id = 1

        mock_item = Mock()

        with patch.object(YourService, 'get_item', return_value=mock_item):
            result = YourService.delete_item(item_id, user_id, hard_delete=False)

            assert result is True
            mock_item.update.assert_called_once_with(is_active=False)

    def test_delete_item_hard_delete(self, db_session):
        """测试硬删除项目"""
        item_id = 1
        user_id = 1

        mock_item = Mock()

        with patch.object(YourService, 'get_item', return_value=mock_item):
            with patch('app.extensions.db.session') as mock_session:
                result = YourService.delete_item(item_id, user_id, hard_delete=True)

                assert result is True
                mock_session.delete.assert_called_once_with(mock_item)
                mock_session.commit.assert_called_once()
```

```python
# tests/integration/test_your_api.py
"""
Your API 集成测试
"""

import json
import pytest

from app.models.user import User
from app.models.your_model import YourModel


class TestYourAPI:
    """YourAPI 集成测试类"""

    def test_create_item_success(self, client, auth_headers):
        """测试成功创建项目"""
        data = {
            'name': 'Test Item',
            'description': 'Test Description'
        }

        response = client.post(
            '/api/your-items',
            data=json.dumps(data),
            headers=auth_headers,
            content_type='application/json'
        )

        assert response.status_code == 201
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['item']['name'] == data['name']

    def test_create_item_validation_error(self, client, auth_headers):
        """测试创建项目时的验证错误"""
        data = {}  # 缺少必需字段

        response = client.post(
            '/api/your-items',
            data=json.dumps(data),
            headers=auth_headers,
            content_type='application/json'
        )

        assert response.status_code == 400
        response_data = json.loads(response.data)
        assert response_data['success'] is False

    def test_get_items_success(self, client, auth_headers, sample_items):
        """测试成功获取项目列表"""
        response = client.get('/api/your-items', headers=auth_headers)

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert 'items' in response_data['data']
        assert 'pagination' in response_data['data']

    def test_get_item_success(self, client, auth_headers, sample_item):
        """测试成功获取项目详情"""
        response = client.get(f'/api/your-items/{sample_item.id}', headers=auth_headers)

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['item']['id'] == sample_item.id

    def test_get_item_not_found(self, client, auth_headers):
        """测试获取不存在的项目"""
        response = client.get('/api/your-items/999', headers=auth_headers)

        assert response.status_code == 404
        response_data = json.loads(response.data)
        assert response_data['success'] is False

    def test_update_item_success(self, client, auth_headers, sample_item):
        """测试成功更新项目"""
        data = {'name': 'Updated Name'}

        response = client.put(
            f'/api/your-items/{sample_item.id}',
            data=json.dumps(data),
            headers=auth_headers,
            content_type='application/json'
        )

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True
        assert response_data['data']['item']['name'] == data['name']

    def test_delete_item_success(self, client, auth_headers, sample_item):
        """测试成功删除项目"""
        response = client.delete(f'/api/your-items/{sample_item.id}', headers=auth_headers)

        assert response.status_code == 200
        response_data = json.loads(response.data)
        assert response_data['success'] is True

    def test_unauthorized_access(self, client):
        """测试未授权访问"""
        response = client.get('/api/your-items')

        assert response.status_code == 401
        response_data = json.loads(response.data)
        assert response_data['success'] is False


@pytest.fixture
def sample_item(db_session, test_user):
    """创建测试项目"""
    item = YourModel.create(
        name='Test Item',
        description='Test Description',
        user_id=test_user.id
    )
    return item


@pytest.fixture
def sample_items(db_session, test_user):
    """创建多个测试项目"""
    items = []
    for i in range(5):
        item = YourModel.create(
            name=f'Test Item {i+1}',
            description=f'Test Description {i+1}',
            user_id=test_user.id
        )
        items.append(item)
    return items
```

## 📝 集成步骤

### 1. 注册蓝图和命名空间

在 `app/__init__.py` 中注册你的蓝图和 API 命名空间：

```python
# 导入蓝图
from app.controllers.your_controller import your_bp

# 导入 API 命名空间
from app.api.your_namespace import your_ns

def create_app(config_name):
    # ... 其他代码 ...

    # 注册蓝图
    app.register_blueprint(your_bp, url_prefix='/api')

    # 注册 API 命名空间
    api.add_namespace(your_ns)

    return app
```

### 2. 更新用户模型（如果需要关联）

如果你的功能需要与用户模型关联，在 `app/models/user.py` 中添加关系：

```python
# 在 User 模型中添加
your_models = relationship("YourModel", back_populates="user", cascade="all, delete-orphan")
```

### 3. 创建数据库迁移

```bash
# 创建迁移文件
flask db migrate -m "Add your_model table"

# 应用迁移
flask db upgrade
```

### 4. 更新文档

- 更新 `README.md` 中的功能列表
- 在 `docs/api-guide.md` 中添加新的 API 端点文档
- 更新 Swagger 文档

## 🧪 测试你的功能

```bash
# 运行单元测试
pytest tests/unit/test_your_service.py -v

# 运行集成测试
pytest tests/integration/test_your_api.py -v

# 运行所有测试
make test

# 检查代码覆盖率
pytest --cov=app.services.your_service tests/unit/test_your_service.py
```

## 📚 最佳实践

1. **遵循现有的代码风格和架构模式**
2. **编写全面的测试用例**
3. **添加适当的错误处理和验证**
4. **使用类型提示提高代码可读性**
5. **编写清晰的文档字符串**
6. **考虑性能和安全性**
7. **遵循 RESTful API 设计原则**

## 🔍 代码审查清单

- [ ] 代码遵循项目的编码规范
- [ ] 所有函数都有适当的文档字符串
- [ ] 错误处理完整且合理
- [ ] 输入验证充分
- [ ] 权限检查正确
- [ ] 测试覆盖率达到要求
- [ ] API 文档完整准确
- [ ] 数据库迁移正确
- [ ] 性能考虑合理
- [ ] 安全性检查通过

使用这个模板可以确保你的新功能与现有系统保持一致，并遵循最佳实践。
