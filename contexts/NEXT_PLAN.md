# pystruct: Django-like 선언적 바이너리 파싱 라이브러리

## 1. 개요

### 1.1 목표

Django ORM이 데이터베이스 테이블을 Python 클래스로 선언적으로 정의하듯이, 바이너리 데이터 구조를 선언적으로 정의하고 파싱/직렬화할 수 있는 라이브러리.

### 1.2 핵심 사용 케이스

| 케이스 | 설명 | 예시 |
|--------|------|------|
| 바이너리 분석 | 기존 바이너리 데이터 파싱 및 분석 | FAT 파일시스템 덤프 분석 |
| 데이터 수정 | 파싱 후 일부 필드 수정하여 재직렬화 | 헤더 값 변경 |
| 데이터 생성 | 새로운 바이너리 데이터 생성 | 테스트용 패킷 생성 |
| 퍼징/테스트 | 의도적으로 잘못된 데이터 생성 | 프로토콜 취약점 테스트 |

### 1.3 목표 API

```python
class Packet(Struct):
    class Meta:
        endian = 'little'
        sync_rules = [
            SyncRule('payload_size', from_field='payload', compute=len),
        ]
        validators = [
            Consistency('payload_size', equals=Len('payload')),
        ]
    
    magic = UInt32(default=0xDEADBEEF)
    version = UInt8(default=1)
    payload_size = UInt16()
    payload = Bytes(size=Ref('payload_size'))

# 파싱
packet = Packet.parse(raw_bytes)
print(packet.version)

# 수정 후 직렬화 (자동 동기화)
packet.payload = b'new data'
data = packet.sync().to_bytes()

# 의도적으로 잘못된 데이터 생성 (퍼징)
packet.payload_size = 9999
bad_data = packet.to_bytes()  # 검증 없이 그대로
```

---

## 2. 핵심 원칙

```
┌─────────────────────────────────────────────────────────────┐
│                       핵심 원칙                             │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Dumb by Default                                         │
│     파싱과 직렬화는 기본적으로 "있는 그대로" 동작한다.      │
│     자동 계산이나 검증은 명시적 요청 시에만 수행한다.       │
│                                                             │
│  2. Explicit over Implicit                                  │
│     sync()와 validate()는 항상 명시적으로 호출한다.         │
│     암묵적인 동작은 예측을 어렵게 만든다.                   │
│                                                             │
│  3. Allow Invalid Data                                      │
│     잘못된 데이터도 생성할 수 있어야 한다.                  │
│     퍼징, 테스트, 분석 등에 필수적이다.                     │
│                                                             │
│  4. Declarative First                                       │
│     구조 정의는 선언적으로, 동작은 명시적으로.              │
│     Django의 Meta 클래스 패턴을 따른다.                     │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 3. 아키텍처 개요

```
┌─────────────────────────────────────────────────────────────┐
│                      User Code                              │
│  class MyStruct(Struct): ...                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     StructMeta                              │
│  - 필드 수집 및 정렬                                        │
│  - Meta 클래스 처리                                         │
│  - 디스크립터 설정                                          │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ┌───────────┐   ┌───────────┐   ┌───────────┐
       │  Fields   │   │   Sync    │   │ Validate  │
       │  System   │   │   System  │   │  System   │
       └───────────┘   └───────────┘   └───────────┘
              │               │               │
              └───────────────┼───────────────┘
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Struct Instance                          │
│  - parse() / to_bytes()                                     │
│  - sync() / validate()                                      │
│  - 필드 값 저장 (_data)                                     │
└─────────────────────────────────────────────────────────────┘
```

---

## 4. Field 시스템

### 4.1 BaseField

모든 필드의 기반 클래스.

```
┌─────────────────────────────────────────────────────────────┐
│                      BaseField (ABC)                        │
├─────────────────────────────────────────────────────────────┤
│ Attributes:                                                 │
│   name: str                  # 필드명 (__set_name__에서)    │
│   default: Any               # 기본값                       │
│   required: bool             # 필수 여부 (기본: True)       │
│   validators: List[Callable] # 필드 레벨 검증기             │
├─────────────────────────────────────────────────────────────┤
│ Abstract Methods:                                           │
│   get_size(instance) -> int  # 바이트 크기                  │
│   parse(buffer, instance) -> Any                            │
│   serialize(value, instance) -> bytes                       │
├─────────────────────────────────────────────────────────────┤
│ Concrete Methods:                                           │
│   validate(value) -> None    # 필드 레벨 검증               │
│   __set_name__(owner, name)  # 디스크립터 프로토콜          │
│   __get__(instance, owner)   # 디스크립터 프로토콜          │
│   __set__(instance, value)   # 디스크립터 프로토콜          │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 필드 계층 구조

```
BaseField
    │
    ├── FixedField                    # 고정 크기 필드
    │       │
    │       ├── IntegerField
    │       │       ├── Int8, UInt8
    │       │       ├── Int16, UInt16
    │       │       ├── Int32, UInt32
    │       │       └── Int64, UInt64
    │       │
    │       ├── FloatField
    │       │       ├── Float32
    │       │       └── Float64
    │       │
    │       ├── FixedBytes            # 고정 길이 바이트
    │       │
    │       ├── FixedString           # 고정 길이 문자열
    │       │
    │       └── Bool
    │
    ├── VariableField                 # 가변 크기 필드
    │       │
    │       ├── Bytes                 # size=int|Ref
    │       │
    │       ├── String                # length=int|Ref
    │       │
    │       ├── PrefixedBytes         # 길이 프리픽스 포함
    │       │
    │       ├── PrefixedString
    │       │
    │       └── NullTerminatedString
    │
    ├── CompositeField                # 복합 필드
    │       │
    │       ├── Array                 # count=int|Ref
    │       │
    │       ├── EmbeddedStruct        # 중첩 구조체 (내부용, 자동 생성)
    │       │
    │       └── Conditional           # 조건부 필드
    │
    ├── SpecialField                  # 특수 필드
    │       │
    │       ├── Padding               # 패딩 바이트
    │       │
    │       ├── Flags                 # 비트 플래그
    │       │
    │       └── Enum                  # 열거형
    │
    └── BitField                      # 비트 단위 필드 (BitStruct 전용)
            │
            ├── Bit                   # 1비트, bool
            │
            └── Bits                  # N비트, int
            
            ※ BitField는 BitStruct에서만 사용 가능
            ※ Struct에서 Bit/Bits 사용 시 StructDefinitionError


BitStruct (Struct와 별개의 기반 클래스)
    │
    ├── BitField들만 포함 가능 (Bit, Bits)
    ├── 바이트 필드(UInt8 등) 사용 시 StructDefinitionError
    └── Meta.size로 총 바이트 크기 지정 필수
```

### 4.3 고정 크기 필드 상세

```python
class FixedField(BaseField):
    """컴파일 타임에 크기가 결정되는 필드"""
    size: int  # 클래스 변수로 고정 크기 정의
    
    def get_size(self, instance) -> int:
        return self.size


class UInt16(FixedField):
    size = 2
    
    def __init__(
        self,
        default: int = 0,
        endian: str = None,  # None이면 Struct의 endian 사용
        validators: List = None,
    ):
        self.default = default
        self.endian = endian
        self.validators = validators or []
    
    def parse(self, buffer: BinaryIO, instance) -> int:
        data = buffer.read(2)
        if len(data) < 2:
            raise UnexpectedEOF(expected=2, got=len(data))
        
        endian = self.endian or instance._meta.endian
        fmt = '<H' if endian == 'little' else '>H'
        return struct.unpack(fmt, data)[0]
    
    def serialize(self, value: int, instance) -> bytes:
        endian = self.endian or instance._meta.endian
        fmt = '<H' if endian == 'little' else '>H'
        return struct.pack(fmt, value)


class FixedBytes(FixedField):
    """고정 길이 바이트 필드"""
    
    def __init__(self, length: int, **kwargs):
        self.size = length
        super().__init__(**kwargs)


class FixedString(FixedField):
    """고정 길이 문자열 필드"""
    
    def __init__(
        self,
        length: int,
        encoding: str = 'utf-8',
        padding: bytes = b'\x00',
        **kwargs
    ):
        self.size = length
        self.encoding = encoding
        self.padding = padding
        super().__init__(**kwargs)
    
    def parse(self, buffer: BinaryIO, instance) -> str:
        data = buffer.read(self.size)
        return data.rstrip(self.padding).decode(self.encoding)
    
    def serialize(self, value: str, instance) -> bytes:
        encoded = value.encode(self.encoding)
        if len(encoded) > self.size:
            raise SerializationError(f"String too long: {len(encoded)} > {self.size}")
        return encoded.ljust(self.size, self.padding)
```

### 4.4 가변 크기 필드 상세

```python
class Bytes(BaseField):
    """가변 길이 바이트 필드"""
    
    def __init__(
        self,
        size: int | Ref,
        **kwargs
    ):
        self.size_spec = size
        super().__init__(**kwargs)
    
    def get_size(self, instance) -> int:
        if isinstance(self.size_spec, Ref):
            return self.size_spec.resolve(instance)
        return self.size_spec
    
    def parse(self, buffer: BinaryIO, instance) -> bytes:
        size = self.get_size(instance)
        data = buffer.read(size)
        if len(data) < size:
            raise UnexpectedEOF(expected=size, got=len(data), field=self.name)
        return data
    
    def serialize(self, value: bytes, instance) -> bytes:
        # 크기 검증 없이 그대로 반환 (dumb serialization)
        return value


class Array(BaseField):
    """배열 필드"""
    
    def __init__(
        self,
        item_field: BaseField,
        count: int | Ref,
        **kwargs
    ):
        self.item_field = item_field
        self.count_spec = count
        super().__init__(**kwargs)
    
    def get_count(self, instance) -> int:
        if isinstance(self.count_spec, Ref):
            return self.count_spec.resolve(instance)
        return self.count_spec
    
    def parse(self, buffer: BinaryIO, instance) -> List:
        count = self.get_count(instance)
        items = []
        for _ in range(count):
            item = self.item_field.parse(buffer, instance)
            items.append(item)
        return items
    
    def serialize(self, value: List, instance) -> bytes:
        parts = []
        for item in value:
            parts.append(self.item_field.serialize(item, instance))
        return b''.join(parts)
```

### 4.5 복합 필드 상세

#### 중첩 구조체: 직접 선언

Struct는 별도 래퍼 없이 **직접 필드로 선언**합니다. 메타클래스가 자동으로 처리합니다.

```python
# 선언 방식
class Container(Struct):
    header = Header()      # Struct 인스턴스로 선언
    body = Body()
    
    # 옵션 전달 가능
    footer = Footer(required=False)


# 메타클래스가 내부적으로 EmbeddedStruct로 변환
class EmbeddedStruct(BaseField):
    """중첩 구조체 필드 (내부용 - 메타클래스가 자동 생성)"""
    
    def __init__(self, struct_class: Type['Struct'], **kwargs):
        self.struct_class = struct_class
        super().__init__(**kwargs)
    
    def get_size(self, instance) -> int:
        # 중첩 구조체의 크기는 해당 인스턴스에서 계산
        nested_instance = getattr(instance, self.name, None)
        if nested_instance:
            return nested_instance.get_size()
        return self.struct_class.get_fixed_size() or 0
    
    def parse(self, buffer: BinaryIO, instance) -> 'Struct':
        nested = self.struct_class._parse_stream(buffer, parent=instance)
        return nested
    
    def serialize(self, value: 'Struct', instance) -> bytes:
        return value.to_bytes()
```

**메타클래스에서의 처리:**

```python
class StructMeta(type):
    def __new__(mcs, name, bases, namespace):
        # ...
        
        for key, value in list(namespace.items()):
            # Struct 인스턴스를 EmbeddedStruct로 변환
            if isinstance(value, Struct):
                namespace[key] = EmbeddedStruct(
                    type(value),
                    required=value._init_required,
                    default=value._init_default,
                )
            elif isinstance(value, BaseField):
                # 일반 필드 처리
                pass
```

#### Conditional (조건부 필드)

```python
class Conditional(BaseField):
    """조건부 필드 - 조건 만족 시에만 존재"""
    
    def __init__(
        self,
        field: BaseField,
        when: Callable[['Struct'], bool] | Ref,
        **kwargs
    ):
        self.field = field
        self.condition = when
        super().__init__(**kwargs)
    
    def should_exist(self, instance) -> bool:
        if isinstance(self.condition, Ref):
            return bool(self.condition.resolve(instance))
        return self.condition(instance)
    
    def get_size(self, instance) -> int:
        if self.should_exist(instance):
            return self.field.get_size(instance)
        return 0
    
    def parse(self, buffer: BinaryIO, instance):
        if self.should_exist(instance):
            return self.field.parse(buffer, instance)
        return None
    
    def serialize(self, value, instance) -> bytes:
        if self.should_exist(instance) and value is not None:
            return self.field.serialize(value, instance)
        return b''
```

### 4.6 특수 필드 상세

```python
class Padding(BaseField):
    """패딩 바이트 - 파싱 시 무시, 직렬화 시 채움"""
    
    def __init__(self, size: int, fill: bytes = b'\x00'):
        self.size = size
        self.fill = fill
    
    def get_size(self, instance) -> int:
        return self.size
    
    def parse(self, buffer: BinaryIO, instance) -> None:
        buffer.read(self.size)  # 읽고 버림
        return None
    
    def serialize(self, value, instance) -> bytes:
        return self.fill * self.size


class Flags(BaseField):
    """비트 플래그 필드"""
    
    def __init__(
        self,
        base_type: FixedField,  # UInt8, UInt16 등
        flags: Dict[str, int],  # {'readable': 0, 'writable': 1, ...}
        **kwargs
    ):
        self.base_type = base_type
        self.flags = flags
        super().__init__(**kwargs)
    
    def get_size(self, instance) -> int:
        return self.base_type.get_size(instance)
    
    def parse(self, buffer: BinaryIO, instance) -> FlagSet:
        value = self.base_type.parse(buffer, instance)
        return FlagSet(value, self.flags)
    
    def serialize(self, value: FlagSet | int, instance) -> bytes:
        if isinstance(value, FlagSet):
            value = value.value
        return self.base_type.serialize(value, instance)


class FlagSet:
    """플래그 값을 편리하게 다루기 위한 래퍼"""
    
    def __init__(self, value: int, flags: Dict[str, int]):
        self.value = value
        self._flags = flags
    
    def __getattr__(self, name: str) -> bool:
        if name in self._flags:
            bit = self._flags[name]
            return bool(self.value & (1 << bit))
        raise AttributeError(name)
    
    def __setattr__(self, name: str, val: bool):
        if name.startswith('_') or name == 'value':
            super().__setattr__(name, val)
        elif name in self._flags:
            bit = self._flags[name]
            if val:
                self.value |= (1 << bit)
            else:
                self.value &= ~(1 << bit)
```

---

## 5. Ref 시스템

### 5.1 Ref 클래스

`Ref`는 다른 필드의 현재 값을 **읽기 전용으로 참조**합니다. 동기화나 계산 책임은 없습니다.

```python
class Ref:
    """필드 참조 - 다른 필드의 현재 값을 읽음"""
    
    def __init__(self, path: str):
        """
        Args:
            path: 필드 경로
                  - 'field_name': 같은 레벨 필드
                  - '../field_name': 부모 구조체 필드
                  - '/header/size': 루트에서부터 경로
        """
        self.path = path
    
    def resolve(self, instance: 'Struct') -> Any:
        """인스턴스에서 참조 값을 해석"""
        
        if self.path.startswith('/'):
            # 절대 경로: 루트에서부터
            target = instance._root
            parts = self.path[1:].split('/')
        elif self.path.startswith('../'):
            # 상대 경로: 부모로 이동
            target = instance
            parts = self.path.split('/')
            while parts and parts[0] == '..':
                target = target._parent
                parts.pop(0)
        else:
            # 현재 레벨
            target = instance
            parts = self.path.split('.')
        
        for part in parts:
            target = getattr(target, part)
        
        return target
    
    # 비교 연산자 지원 (Conditional에서 사용)
    def __ge__(self, other) -> 'RefComparison':
        return RefComparison(self, '>=', other)
    
    def __le__(self, other) -> 'RefComparison':
        return RefComparison(self, '<=', other)
    
    def __eq__(self, other) -> 'RefComparison':
        return RefComparison(self, '==', other)


class RefComparison:
    """Ref 비교 결과 - Conditional의 when에 사용"""
    
    def __init__(self, ref: Ref, op: str, value: Any):
        self.ref = ref
        self.op = op
        self.value = value
    
    def evaluate(self, instance: 'Struct') -> bool:
        resolved = self.ref.resolve(instance)
        if self.op == '>=':
            return resolved >= self.value
        elif self.op == '<=':
            return resolved <= self.value
        elif self.op == '==':
            return resolved == self.value
        # ... 기타 연산자
```

### 5.2 Ref 사용 예시

```python
class Packet(Struct):
    version = UInt8()
    payload_size = UInt16()
    
    # 같은 레벨 참조
    payload = Bytes(size=Ref('payload_size'))
    
    # 조건부 필드에서 비교 사용
    extra = Conditional(UInt32(), when=Ref('version') >= 2)


class Container(Struct):
    header = Header()  # 직접 선언
    
    # 중첩 구조체 필드 참조
    data = Bytes(size=Ref('header.data_size'))


class Item(Struct):
    # 부모 참조
    data = Bytes(size=Ref('../item_size'))
```

---

## 6. Struct 시스템

### 6.1 StructMeta (메타클래스)

```python
class StructMeta(type):
    """Struct 클래스의 메타클래스"""
    
    # 필드 선언 순서 추적용 카운터
    _field_counter = 0
    
    def __new__(mcs, name, bases, namespace):
        # 1. 부모 클래스에서 필드 상속
        fields = OrderedDict()
        for base in bases:
            if hasattr(base, '_fields'):
                fields.update(base._fields)
        
        # 2. 현재 클래스의 필드 수집
        current_fields = {}
        for key, value in list(namespace.items()):
            if isinstance(value, BaseField):
                current_fields[key] = value
                value._order = StructMeta._field_counter
                StructMeta._field_counter += 1
        
        # 3. 선언 순서대로 정렬하여 병합
        sorted_fields = sorted(current_fields.items(), key=lambda x: x[1]._order)
        for key, field in sorted_fields:
            fields[key] = field
        
        namespace['_fields'] = fields
        
        # 4. Meta 클래스 처리
        meta = namespace.get('Meta', None)
        namespace['_meta'] = mcs._process_meta(meta, bases)
        
        # 5. 클래스 생성
        cls = super().__new__(mcs, name, bases, namespace)
        
        # 6. 각 필드에 __set_name__ 호출
        for field_name, field in fields.items():
            field.__set_name__(cls, field_name)
        
        return cls
    
    @staticmethod
    def _process_meta(meta, bases) -> 'StructOptions':
        """Meta 클래스를 StructOptions 객체로 변환"""
        
        # 기본값
        options = StructOptions(
            endian='little',
            trailing_data='error',
            sync_rules=[],
            validators=[],
        )
        
        # 부모 Meta 상속
        for base in bases:
            if hasattr(base, '_meta'):
                options.inherit_from(base._meta)
        
        # 현재 Meta 적용
        if meta:
            if hasattr(meta, 'endian'):
                options.endian = meta.endian
            if hasattr(meta, 'trailing_data'):
                options.trailing_data = meta.trailing_data
            if hasattr(meta, 'sync_rules'):
                options.sync_rules.extend(meta.sync_rules)
            if hasattr(meta, 'validators'):
                options.validators.extend(meta.validators)
        
        return options


@dataclass
class StructOptions:
    """Struct의 메타 옵션"""
    endian: str                    # 'little' | 'big'
    trailing_data: str             # 'error' | 'warn' | 'ignore'
    sync_rules: List['SyncRule']
    validators: List['Validator']
    
    def inherit_from(self, parent: 'StructOptions'):
        self.endian = parent.endian
        self.trailing_data = parent.trailing_data
        self.sync_rules = parent.sync_rules.copy()
        self.validators = parent.validators.copy()
```

### 6.2 Struct 기본 클래스

```python
class Struct(metaclass=StructMeta):
    """바이너리 구조체 기본 클래스"""
    
    _fields: OrderedDict[str, BaseField]
    _meta: StructOptions
    
    def __init__(self, _raw: bytes = None, **kwargs):
        """
        Args:
            _raw: 원본 바이너리 데이터 (파싱 시 내부 사용)
            **kwargs: 필드 초기값
        """
        self._data: Dict[str, Any] = {}
        self._raw = _raw
        self._parent: Optional[Struct] = None
        self._root: Struct = self
        
        # 필드 초기화
        for name, field in self._fields.items():
            if name in kwargs:
                self._data[name] = kwargs[name]
            elif field.default is not None:
                self._data[name] = (
                    field.default() if callable(field.default) 
                    else field.default
                )
            elif not field.required:
                self._data[name] = None
            # required이고 값이 없으면 나중에 to_bytes()에서 체크
    
    # === 클래스 메서드 ===
    
    @classmethod
    def parse(
        cls,
        data: bytes,
        allow_trailing: bool = False,
    ) -> 'Self':
        """바이너리 데이터를 파싱하여 인스턴스 생성"""
        stream = BytesIO(data)
        instance = cls._parse_stream(stream)
        instance._raw = data
        
        # Trailing data 처리
        remaining = stream.read()
        if remaining and not allow_trailing:
            policy = cls._meta.trailing_data
            if policy == 'error':
                raise TrailingDataError(len(remaining))
            elif policy == 'warn':
                warnings.warn(f"Ignoring {len(remaining)} trailing bytes")
        
        return instance
    
    @classmethod
    def _parse_stream(
        cls,
        stream: BinaryIO,
        parent: 'Struct' = None,
    ) -> 'Self':
        """스트림에서 파싱 (내부용)"""
        instance = cls.__new__(cls)
        instance._data = {}
        instance._raw = None
        instance._parent = parent
        instance._root = parent._root if parent else instance
        
        for name, field in cls._fields.items():
            value = field.parse(stream, instance)
            instance._data[name] = value
        
        return instance
    
    @classmethod
    def get_fixed_size(cls) -> Optional[int]:
        """고정 크기 반환. 가변이면 None"""
        total = 0
        for field in cls._fields.values():
            if isinstance(field, FixedField):
                total += field.size
            else:
                return None  # 가변 크기 필드 존재
        return total
    
    # === 인스턴스 메서드 ===
    
    def to_bytes(
        self,
        sync: bool = False,
        validate: bool = False,
    ) -> bytes:
        """인스턴스를 바이너리로 직렬화"""
        if sync:
            self.sync()
        
        if validate:
            self.validate()
        
        buffer = BytesIO()
        for name, field in self._fields.items():
            value = self._data.get(name)
            
            if value is None and field.required:
                raise SerializationError(f"Missing required field: {name}")
            
            data = field.serialize(value, self)
            buffer.write(data)
        
        return buffer.getvalue()
    
    def sync(self, fields: List[str] = None) -> 'Self':
        """동기화 규칙에 따라 필드 값 업데이트"""
        for rule in self._meta.sync_rules:
            if fields is None or rule.target in fields:
                rule.apply(self)
        return self
    
    def validate(self) -> 'Self':
        """모든 검증 규칙 실행"""
        errors = []
        
        # 필드 레벨 검증
        for name, field in self._fields.items():
            value = self._data.get(name)
            for validator in field.validators:
                try:
                    validator(value, self)
                except ValidationError as e:
                    errors.append(FieldValidationError(name, e))
        
        # 구조체 레벨 검증
        for validator in self._meta.validators:
            try:
                validator.validate(self)
            except ValidationError as e:
                errors.append(e)
        
        if errors:
            raise ValidationErrors(errors)
        
        return self
    
    def get_size(self) -> int:
        """현재 인스턴스의 직렬화 크기 계산"""
        total = 0
        for name, field in self._fields.items():
            total += field.get_size(self)
        return total
    
    # === 디스크립터 지원 ===
    
    def __getattr__(self, name: str):
        if name.startswith('_'):
            raise AttributeError(name)
        if name in self._fields:
            return self._data.get(name)
        raise AttributeError(name)
    
    def __setattr__(self, name: str, value):
        if name.startswith('_'):
            super().__setattr__(name, value)
        elif name in self.__class__._fields:
            self._data[name] = value
        else:
            super().__setattr__(name, value)
    
    # === 유틸리티 ===
    
    def __repr__(self):
        fields_str = ', '.join(
            f"{name}={getattr(self, name)!r}"
            for name in self._fields
        )
        return f"{self.__class__.__name__}({fields_str})"
    
    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self._data == other._data
    
    def to_dict(self) -> Dict[str, Any]:
        """딕셔너리로 변환"""
        result = {}
        for name in self._fields:
            value = self._data.get(name)
            if isinstance(value, Struct):
                value = value.to_dict()
            elif isinstance(value, list):
                value = [
                    v.to_dict() if isinstance(v, Struct) else v
                    for v in value
                ]
            result[name] = value
        return result
```

---

## 7. Sync 시스템

### 7.1 SyncRule 클래스

```python
class SyncRule:
    """필드 동기화 규칙"""
    
    def __init__(
        self,
        target: str,
        from_field: str = None,
        from_fields: List[str] = None,
        compute: Callable = None,
    ):
        """
        Args:
            target: 업데이트할 필드명
            from_field: 단일 소스 필드 (compute에 값 전달)
            from_fields: 복수 소스 필드 (compute에 값들 전달)
            compute: 계산 함수
                     - from_field 사용 시: compute(value) -> result
                     - from_fields 사용 시: compute(*values) -> result
                     - 둘 다 없을 시: compute(instance) -> result
        """
        self.target = target
        
        if from_field:
            self.sources = [from_field]
        elif from_fields:
            self.sources = from_fields
        else:
            self.sources = []
        
        self.compute = compute
    
    def apply(self, instance: Struct) -> None:
        """규칙을 적용하여 target 필드 업데이트"""
        if self.sources:
            values = [getattr(instance, name) for name in self.sources]
            if len(values) == 1:
                result = self.compute(values[0])
            else:
                result = self.compute(*values)
        else:
            result = self.compute(instance)
        
        setattr(instance, self.target, result)
```

### 7.2 Sync 사용 예시

```python
class Packet(Struct):
    class Meta:
        sync_rules = [
            # 단일 소스: payload 길이 → payload_size
            SyncRule('payload_size', from_field='payload', compute=len),
            
            # 복수 소스: header + payload 크기 → total_size
            SyncRule(
                'total_size',
                from_fields=['header', 'payload'],
                compute=lambda h, p: len(h) + len(p)
            ),
            
            # 인스턴스 전체 참조: CRC32 계산
            SyncRule(
                'checksum',
                compute=lambda self: crc32(self.payload)
            ),
        ]
    
    total_size = UInt32()
    payload_size = UInt16()
    payload = Bytes(size=Ref('payload_size'))
    checksum = UInt32()
```

### 7.3 중첩 구조체 Sync

```python
class Container(Struct):
    class Meta:
        sync_rules = [
            SyncRule('header.payload_size', 
                     from_field='body.data',
                     compute=len),
        ]
    
    header = Header()
    body = Body()
    
    def sync(self, recursive: bool = True) -> 'Self':
        """
        Args:
            recursive: True면 중첩 구조체도 sync
        """
        if recursive:
            if isinstance(self.header, Struct):
                self.header.sync()
            if isinstance(self.body, Struct):
                self.body.sync()
        
        # 부모 sync 호출
        super().sync()
        return self
```

---

## 8. Validate 시스템

### 8.1 Validator 인터페이스

```python
class Validator(ABC):
    """검증기 기본 클래스"""
    
    @abstractmethod
    def validate(self, instance: Struct) -> None:
        """
        검증 실행
        
        Raises:
            ValidationError: 검증 실패 시
        """
        pass


class FieldValidator(ABC):
    """필드 레벨 검증기"""
    
    @abstractmethod
    def __call__(self, value: Any, instance: Struct) -> None:
        """
        필드 값 검증
        
        Args:
            value: 필드 값
            instance: Struct 인스턴스 (cross-field 참조용)
        
        Raises:
            ValidationError: 검증 실패 시
        """
        pass
```

### 8.2 내장 검증기: 필드 레벨

```python
class Range(FieldValidator):
    """숫자 범위 검증"""
    
    def __init__(self, min_val: Number = None, max_val: Number = None):
        self.min_val = min_val
        self.max_val = max_val
    
    def __call__(self, value, instance):
        if self.min_val is not None and value < self.min_val:
            raise ValidationError(f"Value {value} < minimum {self.min_val}")
        if self.max_val is not None and value > self.max_val:
            raise ValidationError(f"Value {value} > maximum {self.max_val}")


class OneOf(FieldValidator):
    """허용 값 목록 검증"""
    
    def __init__(self, choices: List[Any]):
        self.choices = choices
    
    def __call__(self, value, instance):
        if value not in self.choices:
            raise ValidationError(f"Value {value} not in {self.choices}")


class Regex(FieldValidator):
    """정규식 패턴 검증 (문자열)"""
    
    def __init__(self, pattern: str):
        self.pattern = re.compile(pattern)
    
    def __call__(self, value, instance):
        if not self.pattern.match(value):
            raise ValidationError(f"Value does not match pattern {self.pattern.pattern}")


class BytePattern(FieldValidator):
    """바이트 패턴 검증 (매직 넘버 등)"""
    
    def __init__(self, pattern: bytes):
        self.pattern = pattern
    
    def __call__(self, value, instance):
        if not value.startswith(self.pattern):
            raise ValidationError(f"Bytes do not start with expected pattern")
```

### 8.3 내장 검증기: 구조체 레벨

```python
class Consistency(Validator):
    """필드 간 일관성 검증"""
    
    def __init__(
        self,
        field: str,
        equals: 'Expression' = None,
        greater_than: 'Expression' = None,
        less_than: 'Expression' = None,
    ):
        self.field = field
        self.equals = equals
        self.greater_than = greater_than
        self.less_than = less_than
    
    def validate(self, instance: Struct):
        actual = getattr(instance, self.field)
        
        if self.equals is not None:
            expected = self.equals.evaluate(instance)
            if actual != expected:
                raise InconsistencyError(
                    field=self.field,
                    actual=actual,
                    expected=expected,
                )
        
        if self.greater_than is not None:
            threshold = self.greater_than.evaluate(instance)
            if not (actual > threshold):
                raise ValidationError(
                    f"{self.field}={actual} is not > {threshold}"
                )
        
        if self.less_than is not None:
            threshold = self.less_than.evaluate(instance)
            if not (actual < threshold):
                raise ValidationError(
                    f"{self.field}={actual} is not < {threshold}"
                )


class Custom(Validator):
    """커스텀 검증 함수"""
    
    def __init__(
        self,
        func: Callable[[Struct], bool],
        message: str = "Custom validation failed",
    ):
        self.func = func
        self.message = message
    
    def validate(self, instance: Struct):
        if not self.func(instance):
            raise ValidationError(self.message)
```

### 8.4 Expression 헬퍼

```python
class Expression(ABC):
    """검증에 사용되는 표현식"""
    
    @abstractmethod
    def evaluate(self, instance: Struct) -> Any:
        pass
    
    def __add__(self, other: 'Expression') -> 'BinaryOp':
        return BinaryOp(self, '+', other)
    
    def __sub__(self, other: 'Expression') -> 'BinaryOp':
        return BinaryOp(self, '-', other)


class Len(Expression):
    """필드의 길이"""
    
    def __init__(self, field: str):
        self.field = field
    
    def evaluate(self, instance: Struct) -> int:
        value = getattr(instance, self.field)
        return len(value)


class Value(Expression):
    """필드의 값"""
    
    def __init__(self, field: str):
        self.field = field
    
    def evaluate(self, instance: Struct) -> Any:
        return getattr(instance, self.field)


class Const(Expression):
    """상수 값"""
    
    def __init__(self, value: Any):
        self.value = value
    
    def evaluate(self, instance: Struct) -> Any:
        return self.value


class Checksum(Expression):
    """체크섬 계산"""
    
    def __init__(self, field: str, algorithm: str = 'crc32'):
        self.field = field
        self.algorithm = algorithm
    
    def evaluate(self, instance: Struct) -> int:
        data = getattr(instance, self.field)
        if self.algorithm == 'crc32':
            return binascii.crc32(data) & 0xFFFFFFFF
        # 다른 알고리즘 추가 가능
        raise ValueError(f"Unknown algorithm: {self.algorithm}")


class BinaryOp(Expression):
    """이항 연산"""
    
    def __init__(self, left: Expression, op: str, right: Expression):
        self.left = left
        self.op = op
        self.right = right if isinstance(right, Expression) else Const(right)
    
    def evaluate(self, instance: Struct) -> Any:
        left_val = self.left.evaluate(instance)
        right_val = self.right.evaluate(instance)
        
        if self.op == '+':
            return left_val + right_val
        elif self.op == '-':
            return left_val - right_val
        elif self.op == '*':
            return left_val * right_val
        # ... 기타 연산자
```

### 8.5 Validate 사용 예시

```python
class Packet(Struct):
    class Meta:
        validators = [
            # 크기 일관성
            Consistency('payload_size', equals=Len('payload')),
            
            # 체크섬 일관성  
            Consistency('checksum', equals=Checksum('payload', 'crc32')),
            
            # 복합 표현식
            Consistency('total_size', equals=Len('header') + Len('payload')),
            
            # 커스텀 검증
            Custom(
                lambda self: self.version in (1, 2, 3),
                "Unsupported version"
            ),
        ]
    
    version = UInt8(validators=[Range(1, 255)])  # 필드 레벨 검증
    payload_size = UInt16()
    payload = Bytes(size=Ref('payload_size'))
    checksum = UInt32()
```

---

## 9. 파싱/직렬화 플로우

### 9.1 파싱 플로우

```
┌─────────────────────────────────────────────────────────────┐
│               Struct.parse(data, allow_trailing=False)      │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  stream = BytesIO(data)                                     │
│  instance = Struct._parse_stream(stream)                    │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  _parse_stream:                                             │
│    for name, field in _fields.items():                      │
│        value = field.parse(stream, instance)                │
│        instance._data[name] = value                         │
│                                                             │
│  # Ref는 이미 파싱된 필드만 참조 가능                       │
│  # 따라서 필드 선언 순서가 중요함                           │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  Trailing data 처리:                                        │
│    remaining = stream.read()                                │
│    if remaining and not allow_trailing:                     │
│        policy = Meta.trailing_data                          │
│        if policy == 'error': raise TrailingDataError        │
│        if policy == 'warn': warnings.warn(...)              │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  return instance                                            │
│                                                             │
│  # 검증은 수행하지 않음 (dumb parsing)                      │
│  # 검증 원하면: Struct.parse(data).validate()              │
└─────────────────────────────────────────────────────────────┘
```

### 9.2 직렬화 플로우

```
┌─────────────────────────────────────────────────────────────┐
│          instance.to_bytes(sync=False, validate=False)      │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  if sync:                                                   │
│      self.sync()  # 동기화 규칙 적용                        │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  if validate:                                               │
│      self.validate()  # 검증 규칙 실행                      │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  buffer = BytesIO()                                         │
│  for name, field in _fields.items():                        │
│      value = self._data[name]                               │
│      if value is None and field.required:                   │
│          raise SerializationError                           │
│      buffer.write(field.serialize(value, self))             │
│                                                             │
│  # 크기 일관성 검증 안 함 (dumb serialization)              │
│  # 잘못된 데이터도 그대로 직렬화                            │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  return buffer.getvalue()                                   │
└─────────────────────────────────────────────────────────────┘
```

---

## 10. 예외 계층

```
PyStructError
    │
    ├── ParseError
    │       │
    │       ├── UnexpectedEOF
    │       │       "Expected {expected} bytes for '{field}', got {got}"
    │       │
    │       └── TrailingDataError
    │               "{count} bytes remaining after parsing"
    │
    ├── ValidationError
    │       │
    │       ├── FieldValidationError
    │       │       "Field '{field}': {reason}"
    │       │
    │       ├── InconsistencyError
    │       │       "Field '{field}': expected {expected}, got {actual}"
    │       │
    │       └── ValidationErrors (복수)
    │               errors: List[ValidationError]
    │
    └── SerializationError
            "Cannot serialize '{field}': {reason}"
```

```python
class PyStructError(Exception):
    """라이브러리 기본 예외"""
    pass


class ParseError(PyStructError):
    """파싱 중 발생한 예외"""
    pass


class UnexpectedEOF(ParseError):
    """예상보다 데이터가 부족"""
    
    def __init__(self, expected: int, got: int, field: str = None):
        self.expected = expected
        self.got = got
        self.field = field
        
        msg = f"Expected {expected} bytes, got {got}"
        if field:
            msg = f"Field '{field}': {msg}"
        super().__init__(msg)


class TrailingDataError(ParseError):
    """파싱 후 데이터가 남음"""
    
    def __init__(self, count: int):
        self.count = count
        super().__init__(f"{count} bytes remaining after parsing")


class ValidationError(PyStructError):
    """검증 실패"""
    pass


class InconsistencyError(ValidationError):
    """필드 간 불일치"""
    
    def __init__(self, field: str, actual: Any, expected: Any):
        self.field = field
        self.actual = actual
        self.expected = expected
        super().__init__(
            f"Field '{field}': expected {expected}, got {actual}"
        )


class ValidationErrors(ValidationError):
    """복수 검증 오류"""
    
    def __init__(self, errors: List[ValidationError]):
        self.errors = errors
        messages = [str(e) for e in errors]
        super().__init__("Multiple validation errors:\n" + "\n".join(messages))


class SerializationError(PyStructError):
    """직렬화 실패"""
    pass
```

---

## 11. Endianness 처리

### 11.1 우선순위

```
┌────────────────────────────────────────────────────────────┐
│                 Endianness 우선순위                        │
├────────────────────────────────────────────────────────────┤
│                                                            │
│  1. 필드 레벨 (최우선)                                     │
│     UInt32(endian='big')                                   │
│                                                            │
│  2. 구조체 레벨                                            │
│     class Meta:                                            │
│         endian = 'little'                                  │
│                                                            │
│  3. 전역 기본값                                            │
│     pystruct.configure(default_endian='big')           │
│                                                            │
│  4. 시스템 기본값                                          │
│     'little' (x86/x64 기준)                                │
│                                                            │
└────────────────────────────────────────────────────────────┘
```

### 11.2 Endian 상수

```python
class Endian:
    LITTLE = 'little'
    BIG = 'big'
    NATIVE = 'native'
    NETWORK = 'big'  # 네트워크 바이트 순서 = Big Endian
```

### 11.3 필드에서 Endian 적용

```python
class IntegerField(FixedField):
    def _get_endian(self, instance: Struct) -> str:
        # 필드 레벨 우선
        if self.endian:
            return self.endian
        # 구조체 레벨
        if instance and instance._meta.endian:
            return instance._meta.endian
        # 전역 기본값
        return _global_config.default_endian or 'little'
    
    def _get_format(self, instance: Struct) -> str:
        endian = self._get_endian(instance)
        prefix = '<' if endian == 'little' else '>'
        return prefix + self.format_char
```

---

## 12. 고급 기능

### 12.1 BitStruct (비트 필드)

비트 단위로 필드를 정의할 때 사용합니다. 바이트 경계와 무관하게 연속적으로 비트를 소모합니다.

#### Struct와 BitStruct의 분리 원칙

```
┌─────────────────────────────────────────────────────────────┐
│  Struct: 바이트 단위 필드만 허용                            │
│    - UInt8, UInt16, Bytes, String, Array, ...              │
│    - Bit, Bits 사용 불가                                    │
│    - 항상 바이트 경계에서 동작                              │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  BitStruct: 비트 단위 필드만 허용                           │
│    - Bit(), Bits(n) 만 가능                                 │
│    - UInt8, Bytes 등 바이트 필드 사용 불가                  │
│    - 바이트가 필요하면 Bits(8)로 표현                       │
└─────────────────────────────────────────────────────────────┘
```

**메타클래스에서 검증:**

```python
class StructMeta(type):
    def __new__(mcs, name, bases, namespace):
        # ... 필드 수집 ...
        
        for field_name, field in fields.items():
            if isinstance(field, (Bit, Bits)):
                raise StructDefinitionError(
                    f"Struct '{name}' cannot contain bit fields. "
                    f"Use BitStruct for bit-level fields. "
                    f"(field: {field_name})"
                )


class BitStructMeta(type):
    def __new__(mcs, name, bases, namespace):
        # ... 필드 수집 ...
        
        for field_name, field in fields.items():
            if not isinstance(field, (Bit, Bits)):
                raise StructDefinitionError(
                    f"BitStruct '{name}' can only contain Bit or Bits fields. "
                    f"Use Bits(8) instead of UInt8, etc. "
                    f"(field: {field_name}, type: {type(field).__name__})"
                )
```

**잘못된 사용 예:**

```python
# ❌ 오류: Struct에서 Bits 사용
class InvalidStruct(Struct):
    flags = Bits(4)      # StructDefinitionError!
    value = UInt8()

# ❌ 오류: BitStruct에서 UInt8 사용  
class InvalidBitStruct(BitStruct):
    class Meta:
        size = 2
    
    flags = Bits(4)
    value = UInt8()      # StructDefinitionError!
```

**올바른 사용:**

```python
# ✅ BitStruct: 비트 필드만
class Flags(BitStruct):
    class Meta:
        size = 2
    
    reserved = Bits(4)
    value = Bits(8)      # 바이트가 필요하면 Bits(8)
    rest = Bits(4)


# ✅ Struct: 바이트 필드만, BitStruct 포함 가능
class Packet(Struct):
    header = UInt32()
    flags = Flags()      # BitStruct를 필드로 포함
    payload = Bytes(size=Ref('length'))
```

#### 비트 소모 방식

```
예: 2바이트 (16비트) 데이터 0xE3 0x28
    
바이트 레이아웃 (MSB first 가정):
    바이트 0 (0xE3): 1 1 1 0  0 0 1 1
    바이트 1 (0x28): 0 0 1 0  1 0 0 0
    
비트 인덱스:        7 6 5 4  3 2 1 0  15 14 13 12  11 10 9 8

class Example(BitStruct):
    class Meta:
        size = 2  # 총 바이트 크기
        bit_order = 'msb'  # 'msb' (기본) 또는 'lsb'
    
    a = Bits(4)   # 비트 7-4 → 0b1110 = 14
    b = Bits(4)   # 비트 3-0 → 0b0011 = 3
    c = Bits(5)   # 비트 15-11 → 0b00101 = 5
    d = Bits(3)   # 비트 10-8 → 0b000 = 0

result = Example.parse(bytes([0xE3, 0x28]))
# result.a = 14 (0xE)
# result.b = 3  (0x3)
# result.c = 5  (0b00101)
# result.d = 0  (0b000)
```

#### 실제 사용 예: TCP 플래그

```
TCP 헤더의 Data Offset + Flags (2바이트):

    비트 15-12: Data Offset (4비트)
    비트 11-9:  Reserved (3비트)
    비트 8-0:   Flags (9비트: NS, CWR, ECE, URG, ACK, PSH, RST, SYN, FIN)

바이트 레이아웃:
    [DDDD RRR N] [CWEU APRS F]
     ^^^^ ^^^ ^   ^^^^ ^^^^ ^
     |    |   |   |    |    └─ FIN
     |    |   |   |    └────── SYN, RST, PSH, ACK
     |    |   |   └─────────── URG, ECE, CWR
     |    |   └─────────────── NS
     |    └─────────────────── Reserved
     └──────────────────────── Data Offset
```

```python
class TCPDataOffsetAndFlags(BitStruct):
    class Meta:
        size = 2
    
    data_offset = Bits(4)  # 4비트: 헤더 길이 (32비트 워드 단위)
    reserved = Bits(3)     # 3비트: 예약
    ns = Bit()             # 1비트: ECN-nonce
    cwr = Bit()            # 1비트
    ece = Bit()            # 1비트
    urg = Bit()            # 1비트
    ack = Bit()            # 1비트
    psh = Bit()            # 1비트
    rst = Bit()            # 1비트
    syn = Bit()            # 1비트
    fin = Bit()            # 1비트
    # 총 16비트 = 2바이트


class TCPHeader(Struct):
    src_port = UInt16()
    dst_port = UInt16()
    seq_num = UInt32()
    ack_num = UInt32()
    offset_flags = TCPDataOffsetAndFlags()  # BitStruct 직접 선언
    window = UInt16()
    checksum = UInt16()
    urgent_ptr = UInt16()


# 파싱 예시
data = bytes([
    0x00, 0x50,  # src_port = 80
    0x1F, 0x90,  # dst_port = 8080
    0x00, 0x00, 0x00, 0x01,  # seq_num
    0x00, 0x00, 0x00, 0x00,  # ack_num
    0x50, 0x02,  # offset_flags: data_offset=5, SYN=1
    0xFF, 0xFF,  # window
    0x00, 0x00,  # checksum
    0x00, 0x00,  # urgent_ptr
])

tcp = TCPHeader.parse(data)
print(tcp.offset_flags.data_offset)  # 5 (20바이트 헤더)
print(tcp.offset_flags.syn)          # True
print(tcp.offset_flags.ack)          # False
```

#### BitStruct 직렬화

```python
# 값 설정 후 직렬화
flags = TCPDataOffsetAndFlags()
flags.data_offset = 5
flags.syn = True
flags.ack = True

raw = flags.to_bytes()  # b'\x50\x12' (SYN+ACK)
```

#### Bit vs Bits

```python
class Example(BitStruct):
    class Meta:
        size = 1
    
    flag1 = Bit()           # 1비트, bool로 파싱
    flag2 = Bit()           # 1비트, bool로 파싱  
    value = Bits(6)         # 6비트, int로 파싱

# Bit()은 Bits(1)의 편의 별칭이지만, bool로 자동 변환
```

#### 바이트 경계 검증

```python
class Invalid(BitStruct):
    class Meta:
        size = 1  # 8비트
    
    a = Bits(5)
    b = Bits(5)  # 오류: 총 10비트 > 8비트

# StructDefinitionError: BitStruct 'Invalid' requires 10 bits 
#                        but Meta.size specifies 8 bits (1 byte)
```

### 12.2 Switch (타입 분기)

```python
class Message(Struct):
    msg_type = UInt8()
    
    # msg_type 값에 따라 다른 구조체 사용
    payload = Switch(
        on=Ref('msg_type'),
        cases={
            1: TextMessage(),
            2: ImageMessage(),
            3: FileMessage(),
        },
        default=Bytes(size=Ref('remaining_size')),
    )
```

---

## 13. 확장 포인트

### 13.1 커스텀 필드 정의

```python
class IPv4Address(FixedField):
    """4바이트를 IPv4 주소 문자열로 변환"""
    
    size = 4
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
    
    def parse(self, buffer: BinaryIO, instance) -> str:
        data = buffer.read(4)
        if len(data) < 4:
            raise UnexpectedEOF(expected=4, got=len(data), field=self.name)
        return '.'.join(str(b) for b in data)
    
    def serialize(self, value: str, instance) -> bytes:
        parts = [int(p) for p in value.split('.')]
        return bytes(parts)


class MACAddress(FixedField):
    """6바이트 MAC 주소"""
    
    size = 6
    
    def parse(self, buffer: BinaryIO, instance) -> str:
        data = buffer.read(6)
        return ':'.join(f'{b:02x}' for b in data)
    
    def serialize(self, value: str, instance) -> bytes:
        parts = value.split(':')
        return bytes(int(p, 16) for p in parts)
```

### 13.2 커스텀 검증기 정의

```python
class IPInRange(FieldValidator):
    """IP 주소 범위 검증"""
    
    def __init__(self, network: str):
        import ipaddress
        self.network = ipaddress.ip_network(network)
    
    def __call__(self, value: str, instance):
        import ipaddress
        ip = ipaddress.ip_address(value)
        if ip not in self.network:
            raise ValidationError(f"IP {value} not in {self.network}")


# 사용
class Config(Struct):
    server_ip = IPv4Address(validators=[IPInRange('192.168.0.0/16')])
```

---

## 14. 전체 사용 예시

### 14.1 간단한 패킷

```python
from pystruct import (
    Struct, UInt8, UInt16, UInt32, Bytes, Ref,
    SyncRule, Consistency, Len, Range,
)

class SimplePacket(Struct):
    class Meta:
        endian = 'big'  # 네트워크 바이트 순서
        sync_rules = [
            SyncRule('length', from_field='data', compute=len),
        ]
        validators = [
            Consistency('length', equals=Len('data')),
        ]
    
    magic = UInt32(default=0xCAFEBABE)
    version = UInt8(default=1, validators=[Range(1, 10)])
    length = UInt16()
    data = Bytes(size=Ref('length'))


# === 파싱 ===
raw = bytes([
    0xCA, 0xFE, 0xBA, 0xBE,  # magic
    0x01,                     # version
    0x00, 0x05,               # length = 5
    0x48, 0x65, 0x6C, 0x6C, 0x6F,  # "Hello"
])

packet = SimplePacket.parse(raw)
print(packet.data)  # b'Hello'


# === 검증 포함 파싱 ===
packet = SimplePacket.parse(raw).validate()


# === 수정 후 직렬화 ===
packet.data = b'World!'
new_raw = packet.sync().to_bytes()
# length가 자동으로 6으로 업데이트됨


# === 새로 생성 ===
packet = SimplePacket(data=b'Test')
raw = packet.sync().to_bytes()


# === 퍼징: 일부러 잘못된 데이터 ===
packet = SimplePacket(
    magic=0xDEADDEAD,
    version=255,
    length=1000,  # 잘못된 길이
    data=b'x',
)
bad_raw = packet.to_bytes()  # 검증 없이 생성
```

### 14.2 중첩 구조체

```python
class Header(Struct):
    class Meta:
        endian = 'little'
    
    magic = UInt32(default=0xDEADBEEF)
    version = UInt16(default=1)
    flags = UInt16()
    payload_size = UInt32()


class Payload(Struct):
    item_count = UInt16()
    items = Array(UInt32(), count=Ref('item_count'))
    
    class Meta:
        sync_rules = [
            SyncRule('item_count', from_field='items', compute=len),
        ]


class Container(Struct):
    header = Header()      # 직접 선언
    payload = Payload()    # 직접 선언
    checksum = UInt32()
    
    class Meta:
        sync_rules = [
            SyncRule('header.payload_size',
                     compute=lambda self: self.payload.get_size()),
            SyncRule('checksum',
                     compute=lambda self: crc32(self.payload.to_bytes())),
        ]
        validators = [
            Consistency('header.payload_size',
                        equals=Value('payload').method('get_size')),
        ]


# 사용
container = Container(
    header=Header(),
    payload=Payload(items=[1, 2, 3, 4, 5]),
)
container.sync(recursive=True)
data = container.to_bytes()
```

### 14.3 조건부 필드

```python
class VersionedPacket(Struct):
    version = UInt8()
    
    # version >= 2일 때만 존재
    extra_flags = Conditional(
        UInt16(),
        when=Ref('version') >= 2
    )
    
    data_size = UInt16()
    data = Bytes(size=Ref('data_size'))


# 버전 1: extra_flags 없음
v1_data = bytes([0x01, 0x00, 0x03, 0x41, 0x42, 0x43])
p1 = VersionedPacket.parse(v1_data)
assert p1.extra_flags is None
assert p1.data == b'ABC'

# 버전 2: extra_flags 있음
v2_data = bytes([0x02, 0xFF, 0x00, 0x00, 0x03, 0x41, 0x42, 0x43])
p2 = VersionedPacket.parse(v2_data)
assert p2.extra_flags == 0x00FF
assert p2.data == b'ABC'
```

---

## 15. 구현 계획

### Phase 1: 핵심 (MVP)

- [ ] BaseField, FixedField
- [ ] 정수 필드: Int8, UInt8, Int16, UInt16, Int32, UInt32, Int64, UInt64
- [ ] StructMeta, Struct 기본 클래스
- [ ] parse(), to_bytes() 기본 구현
- [ ] Ref 기본 구현

### Phase 2: 가변 필드

- [ ] Bytes, String (with Ref)
- [ ] Array (with Ref)
- [ ] FixedBytes, FixedString

### Phase 3: Sync 시스템

- [ ] SyncRule
- [ ] sync() 메서드
- [ ] to_bytes(sync=True)

### Phase 4: Validate 시스템

- [ ] FieldValidator 인터페이스
- [ ] 내장 검증기: Range, OneOf, Regex
- [ ] Consistency, Custom
- [ ] Expression: Len, Value, Checksum
- [ ] validate() 메서드

### Phase 5: 복합 필드

- [ ] EmbeddedStruct (메타클래스 자동 변환)
- [ ] Conditional
- [ ] Switch

### Phase 6: 특수 필드

- [ ] Padding
- [ ] Flags, FlagSet
- [ ] Enum

### Phase 7: 고급 기능

- [ ] BitStruct

### Phase 8: 완성도

- [ ] 상세한 에러 메시지
- [ ] 타입 힌트 완성
- [ ] 문서화
- [ ] 테스트 커버리지
- [ ] 성능 최적화

---

## 16. 설계 결정 요약

| 항목 | 결정 | 이유 |
|------|------|------|
| 기본 동작 | Dumb (있는 그대로) | 퍼징, 분석, 유연성 |
| 자동 계산 | 명시적 sync() | 예측 가능한 동작 |
| 검증 | 명시적 validate() | 잘못된 데이터도 허용 |
| 메타 정보 | class Meta | Django 스타일 일관성 |
| 필드 참조 | Ref (읽기 전용) | 단순함, 명확한 방향성 |
| 동기화 규칙 | Meta.sync_rules | 선언적 정의 |
| 검증 규칙 | Meta.validators | 선언적 정의 |
| Dirty tracking | 없음 | 불필요 (dumb 원칙) |
| Endianness | 3단계 우선순위 | 유연성과 편의성 |
