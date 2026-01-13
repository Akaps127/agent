'use client';

import { useState, useEffect } from 'react';
import {
  AppShell, Container, Title, Paper, Group, Button,
  TextInput, NumberInput, Grid, Badge, Text, Select, Switch, Alert, ThemeIcon, Stepper, Stack, Box, Textarea, Tabs,
  PasswordInput, Center, Card, Image
} from '@mantine/core';
import { useForm } from '@mantine/form';
import { Dropzone, FileWithPath } from '@mantine/dropzone';
import { IconUpload, IconFile, IconX, IconCheck, IconArrowRight, IconPencil, IconDownload, IconFileCheck, IconLock, IconLogin, IconLogout } from '@tabler/icons-react';
import { Notifications, notifications } from '@mantine/notifications';
import axios from 'axios';

// API Base URL - 개발환경에서는 localhost:8000, 배포환경에서는 상대경로 사용
const API_BASE = typeof window !== 'undefined' && window.location.port === '3000'
  ? 'http://localhost:8000'
  : '';

// 법령 기준 금액 상수
const GOSI_AMOUNT = 230000000;   // 2.3억 (고시금액)
const SMALL_SUM_LIMIT = 100000000; // 1억 (소액수의 한도)

// 📅 날짜 계산 헬퍼 함수
const formatDateTime = (date: Date, hour: number, minute: number): string => {
  const y = date.getFullYear();
  const m = String(date.getMonth() + 1).padStart(2, '0');
  const d = String(date.getDate()).padStart(2, '0');
  const hh = String(hour).padStart(2, '0');
  const mm = String(minute).padStart(2, '0');
  return `${y}-${m}-${d} ${hh}:${mm}`;
};

const addBusinessDays = (startDate: Date, days: number): Date => {
  let currentDate = new Date(startDate);
  let daysAdded = 0;
  while (daysAdded < days) {
    currentDate.setDate(currentDate.getDate() + 1);
    const dayOfWeek = currentDate.getDay();
    // Skip weekends (0 = Sunday, 6 = Saturday)
    if (dayOfWeek !== 0 && dayOfWeek !== 6) {
      daysAdded++;
    }
  }
  return currentDate;
};

const calculateDefaultBidDates = (isSmallSum: boolean): { start: string; end: string; opening: string } => {
  const today = new Date();
  let openingDate: Date;

  if (isSmallSum) {
    // 소액수의: 3 영업일
    openingDate = addBusinessDays(today, 3);
  } else {
    // 적격심사: 7 달력일
    openingDate = new Date(today);
    openingDate.setDate(openingDate.getDate() + 7);
  }

  return {
    start: formatDateTime(today, 9, 0),
    end: formatDateTime(openingDate, 10, 0),
    opening: formatDateTime(openingDate, 11, 0),
  };
};


// Type definition for the form
interface FormValues {
  notice_name: string;
  budget_total: number;
  budget_supply: number;
  item_codes: string;    // Treated as string for CSV input
  industry_codes: string;
  industry_names: string;  // 업종명
  law_basis: string;       // 근거법령
  law_article: string;     // 법령조항
  item_names: string;    // Treated as string for CSV input
  delivery_period_text: string;
  contract_method_text: string;
  region_restriction_text: string | null;
  sme_restriction_text: string;
  joint_venture_allow: boolean;
  project_contact: string;
  contract_contact: string;
  // NEW: Bid date fields
  bid_submission_start: string;
  bid_submission_end: string;
  bid_opening_datetime: string;
  bid_opening_place: string;
  // NEW: 4대 파라미터
  contract_law_type: string;      // 계약법 구분
  contract_type: string;          // 계약 유형
  bidding_method: string;         // 입찰 방법
  winner_determination: string;   // 낙찰자결정방법
}

// 4대 파라미터 정의 타입
interface ParameterDefinition {
  name: string;
  display_name: string;
  values: string[];
  info: Record<string, any>;
  default: string | null;
}

interface ParametersData {
  contract_law_types: ParameterDefinition;
  contract_types: ParameterDefinition;
  bidding_methods: ParameterDefinition;
  winner_methods: ParameterDefinition;
}

export default function Home() {
  const [activeStep, setActiveStep] = useState(0);
  const [file, setFile] = useState<FileWithPath | null>(null);
  const [loading, setLoading] = useState(false);
  const [htmlContent, setHtmlContent] = useState<string | null>(null);
  const [docxFilename, setDocxFilename] = useState<string | null>(null);
  const [isEditingHtml, setIsEditingHtml] = useState(false); // HTML 편집 모드
  const [verificationReport, setVerificationReport] = useState<any>(null); // 검증 결과

  // 🔐 로그인 상태
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [loginId, setLoginId] = useState('');
  const [loginPw, setLoginPw] = useState('');

  const handleLogin = () => {
    // 간단한 데모 로그인 로직
    if (loginId && loginPw) {
      setIsLoggedIn(true);
      notifications.show({
        title: '환영합니다',
        message: '성공적으로 로그인되었습니다.',
        color: 'teal',
        icon: <IconCheck size={18} />,
      });
    } else {
      notifications.show({
        title: '로그인 실패',
        message: '아이디와 비밀번호를 입력해주세요.',
        color: 'red',
        icon: <IconX size={18} />,
      });
    }
  };

  const handleLogout = () => {
    setIsLoggedIn(false);
    setLoginId('');
    setLoginPw('');
    setActiveStep(0); // Reset steps
    setFile(null);
    notifications.show({
      title: '로그아웃',
      message: '로그아웃 되었습니다.',
      color: 'blue',
    });
  };

  // 🎯 4대 파라미터 정의 (서버에서 가져옴)
  const [parameters, setParameters] = useState<ParametersData | null>(null);
  const [availableBiddingMethods, setAvailableBiddingMethods] = useState<string[]>([]);

  // 파라미터 정의 가져오기
  useEffect(() => {
    const fetchParameters = async () => {
      try {
        const response = await axios.get(`${API_BASE}/parameters`);
        setParameters(response.data);
        console.log('[Parameters] Loaded:', response.data);
      } catch (error) {
        console.error('[Parameters] Failed to load:', error);
      }
    };
    fetchParameters();
  }, []);

  // Mantine Form
  const form = useForm<FormValues>({
    initialValues: {
      notice_name: "",
      budget_total: 0,
      budget_supply: 0,
      item_codes: "",
      industry_codes: "",
      industry_names: "",
      law_basis: "",
      law_article: "",
      item_names: "",
      delivery_period_text: "",
      contract_method_text: "",
      region_restriction_text: "", // 지역제한
      sme_restriction_text: "",    // 기업제한 (자동계산)
      joint_venture_allow: false,
      project_contact: "",
      contract_contact: "",
      // NEW: Bid date fields (empty = auto-calculate)
      bid_submission_start: "",
      bid_submission_end: "",
      bid_opening_datetime: "",
      bid_opening_place: "국가종합전자조달시스템(나라장터)",
      // NEW: 4대 파라미터 기본값
      contract_law_type: "국가계약법",
      contract_type: "물품구매",
      bidding_method: "제한경쟁",
      winner_determination: "소액수의",
    },
    validate: {
      notice_name: (value) => (value ? null : '공고명은 필수입니다'),
      budget_supply: (value) => (value > 0 ? null : '공급가액은 0보다 커야 합니다'),
    },
  });

  // 🔄 낙찰자결정방법 변경 시 입찰방법 자동 업데이트
  useEffect(() => {
    const updateBiddingMethod = async () => {
      if (!form.values.winner_determination) return;

      try {
        // 소액수의인 경우 자동으로 수의계약으로 설정
        if (form.values.winner_determination === '소액수의') {
          form.setFieldValue('bidding_method', '수의계약');
          setAvailableBiddingMethods(['수의계약']);
        } else if (form.values.winner_determination === '적격심사') {
          // 적격심사인 경우 수의계약 제외
          setAvailableBiddingMethods(['일반경쟁', '제한경쟁', '지명경쟁']);
          // 현재 수의계약이면 제한경쟁으로 변경
          if (form.values.bidding_method === '수의계약') {
            form.setFieldValue('bidding_method', '제한경쟁');
          }
        }
      } catch (error) {
        console.error('[Parameters] Failed to update bidding method:', error);
      }
    };

    updateBiddingMethod();
  }, [form.values.winner_determination]);

  // 🔄 [핵심 로직] 예산 변경 감지 및 강제 설정
  useEffect(() => {
    // 1. 지역제한은 항상 전국으로 고정
    if (form.values.region_restriction_text !== '전국') {
      form.setFieldValue('region_restriction_text', '전국');
    }

  }, [form.values.budget_supply]); // budget_supply가 변할 때마다 실행

  // Step 1: Upload PDF/HWP & Extract
  const handleExtract = async () => {
    if (!file) return;

    setLoading(true);
    const fileExt = file.name.split('.').pop()?.toLowerCase();
    const id = notifications.show({
      loading: true,
      title: '문서 분석 중',
      message: `${fileExt === 'hwp' ? 'HWP' : 'PDF'}에서 정보를 추출하고 있습니다...`,
      autoClose: false,
      withCloseButton: false,
    });

    try {
      const formData = new FormData();
      formData.append('file', file);

      const response = await axios.post(`${API_BASE}/extract`, formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });

      const data = response.data;

      // 📅 소액수의 여부 판단 후 기본 날짜 계산
      const budgetSupply = data.budget_supply || 0;
      const contractMethodText = data.contract_method_text || '';
      const isSmallSum = budgetSupply <= SMALL_SUM_LIMIT &&
        (contractMethodText.includes('소액') || !contractMethodText.includes('일반'));
      const defaultDates = calculateDefaultBidDates(isSmallSum);

      // Populate Form
      form.setValues({
        notice_name: data.notice_name || '',
        budget_total: data.budget_total || 0,
        budget_supply: data.budget_supply || 0,
        item_codes: data.item_codes ? data.item_codes.join(', ') : '',
        item_names: data.item_names ? data.item_names.join(', ') : '',
        delivery_period_text: data.delivery_period_text || '',
        contract_method_text: data.contract_method_text || '',
        region_restriction_text: data.region_restriction_text || '',
        sme_restriction_text: data.sme_restriction_text || '',
        joint_venture_allow: data.joint_venture_allow || false,
        // New fields
        project_contact: data.project_contact || '',
        contract_contact: data.contract_contact || '',
        industry_codes: data.industry_codes ? data.industry_codes.join(', ') : '',
        industry_names: data.industry_names ? data.industry_names.join(', ') : '',
        law_basis: data.law_basis ? data.law_basis.join(', ') : '',
        law_article: data.law_article ? data.law_article.join(', ') : '',
        // 📅 기본 날짜값 설정 (자동 계산됨)
        bid_submission_start: defaultDates.start,
        bid_submission_end: defaultDates.end,
        bid_opening_datetime: defaultDates.opening,
        bid_opening_place: '국가종합전자조달시스템(나라장터)',
        // ✨ 4대 파라미터 (자동 설정)
        contract_law_type: data.contract_law_type || '국가계약법',
        contract_type: data.contract_type || '물품구매',
        winner_determination: isSmallSum ? '소액수의' : '적격심사',
        bidding_method: isSmallSum ? '수의계약' : '제한경쟁',
      });

      notifications.update({
        id,
        color: 'teal',
        title: '분석 완료',
        message: '추출된 정보를 확인 및 수정해주세요.',
        icon: <IconCheck style={{ width: 18, height: 18 }} />,
        loading: false,
        autoClose: 3000,
      });

      setActiveStep(1); // Go to Edit Step

    } catch (error) {
      console.error(error);
      notifications.update({
        id,
        color: 'red',
        title: '추출 실패',
        message: `${fileExt === 'hwp' ? 'HWP' : 'PDF'} 분석 중 오류가 발생했습니다.`,
        icon: <IconX style={{ width: 18, height: 18 }} />,
        loading: false,
        autoClose: 4000,
      });
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Generate Notice with Edited Data
  const handleGenerate = async () => {
    const validation = form.validate();
    if (validation.hasErrors) return;

    setLoading(true);
    setHtmlContent(null);
    setDocxFilename(null);
    setVerificationReport(null); // 검증 결과 초기화

    // Convert string arrays back to lists
    const payload = {
      plan_data: {
        ...form.values,
        item_codes: form.values.item_codes.split(',').map(s => s.trim()).filter(Boolean),
        item_names: form.values.item_names.split(',').map(s => s.trim()).filter(Boolean),
        industry_codes: form.values.industry_codes.split(',').map(s => s.trim()).filter(Boolean),
        industry_names: form.values.industry_names.split(',').map(s => s.trim()).filter(Boolean),
        law_basis: form.values.law_basis.split(',').map(s => s.trim()).filter(Boolean),
        law_article: form.values.law_article.split(',').map(s => s.trim()).filter(Boolean),
        // Bid date fields: if empty string, send null for auto-calculation
        bid_submission_start: form.values.bid_submission_start || null,
        bid_submission_end: form.values.bid_submission_end || null,
        bid_opening_datetime: form.values.bid_opening_datetime || null,
        bid_opening_place: form.values.bid_opening_place || null,
        // ✨ 4대 파라미터 포함
        contract_law_type: form.values.contract_law_type,
        contract_type: form.values.contract_type,
        bidding_method: form.values.bidding_method,
        winner_determination: form.values.winner_determination,
      },
      enable_verification: true, // 검증 활성화
    };

    const id = notifications.show({
      loading: true,
      title: '공고문 생성 및 검증 중',
      message: '공고문을 작성하고 법령 검증을 수행하고 있습니다...',
      autoClose: false,
      withCloseButton: false,
    });

    try {
      const response = await axios.post(`${API_BASE}/generate_from_data`, payload);

      if (response.data.html_content) {
        setHtmlContent(response.data.html_content);
        setDocxFilename(response.data.docx_filename || null);

        // 검증 결과 저장
        if (response.data.verification) {
          setVerificationReport(response.data.verification);
          console.log('[Verification] Report:', response.data.verification);
        }

        setActiveStep(2); // Go to Result Step

        // 검증 결과에 따른 알림 색상 결정
        const riskLevel = response.data.verification?.overall_risk || 'LOW';
        const notifColor = riskLevel === 'HIGH' ? 'orange' : riskLevel === 'MEDIUM' ? 'yellow' : 'teal';

        notifications.update({
          id,
          color: notifColor,
          title: '생성 완료!',
          message: riskLevel !== 'LOW'
            ? `입찰공고문이 작성되었습니다. ⚠️ 검증 결과: ${riskLevel} 리스크`
            : '입찰공고문 작성 및 검증이 완료되었습니다.',
          icon: <IconCheck style={{ width: 18, height: 18 }} />,
          loading: false,
          autoClose: 5000,
        });
      }


    } catch (error) {
      console.error(error);
      notifications.update({
        id,
        color: 'red',
        title: '오류 발생',
        message: '공고문 생성 중 문제가 발생했습니다.',
        icon: <IconX style={{ width: 18, height: 18 }} />,
        loading: false,
        autoClose: 4000,
      });
    } finally {
      setLoading(false);
    }
  };

  // 🔐 로그인 화면 렌더링
  if (!isLoggedIn) {
    return (
      <Box style={{
        minHeight: '100vh',
        background: 'linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center'
      }}>
        <Paper p={50} radius="lg" shadow="xl" style={{ width: 420, backdropFilter: 'blur(10px)', backgroundColor: 'rgba(255, 255, 255, 0.9)' }}>
          <Stack align="center" mb="xl" gap="xs">
            {/* <ThemeIcon size={80} radius="xl" variant="gradient" gradient={{ from: '#2E86C1', to: '#9BCF53', deg: 135 }}>
              <IconFileCheck size={40} />
            </ThemeIcon> */}
            <Image
              src="/keco_logo.png"
              w={120}
              h="auto"
              fit="contain"
              alt="한국환경공단"
              mb="sm"
            />
            <Title order={2} style={{ color: '#2E86C1', marginTop: 15 }}>한국환경공단</Title>
            <Text c="dimmed" size="sm">지능형 입찰공고 자동 생성 시스템</Text>
          </Stack>

          <form onSubmit={(e) => { e.preventDefault(); handleLogin(); }}>
            <Stack gap="lg">
              <TextInput
                label="아이디"
                placeholder="admin"
                required
                size="md"
                leftSection={<IconLogin size={16} />}
                value={loginId}
                onChange={(e) => setLoginId(e.currentTarget.value)}
              />
              <PasswordInput
                label="비밀번호"
                placeholder="********"
                required
                size="md"
                leftSection={<IconLock size={16} />}
                value={loginPw}
                onChange={(e) => setLoginPw(e.currentTarget.value)}
              />
              <Button fullWidth mt="xl" size="md" type="submit" variant="gradient" gradient={{ from: '#2E86C1', to: '#1c7ed6', deg: 90 }}>
                로그인
              </Button>
              <Text c="dimmed" size="xs" ta="center">
                데모 계정: admin / 1234 (아무 값이나 입력 가능)
              </Text>
            </Stack>
          </form>
        </Paper>
      </Box>
    );
  }

  return (
    <AppShell header={{ height: 60 }} padding="sm">
      <AppShell.Header p="md">
        <Group justify="space-between">
          <Box>
            <Title order={3} style={{
              background: 'linear-gradient(135deg, #9BCF53 0%, #2E86C1 100%)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              fontWeight: 800
            }}>
              한국환경공단
            </Title>
            <Text c="dimmed" size="xs">
              지능형 입찰공고 자동 생성 시스템 (Review Mode)
            </Text>
          </Box>
          {/* Logout Button */}
          <Button variant="subtle" color="gray" size="sm" onClick={handleLogout} leftSection={<IconLogout size={16} />}>
            로그아웃
          </Button>
        </Group>
      </AppShell.Header>

      <AppShell.Main bg="#f8fbfc">
        <Container fluid px="xs" style={{ width: '100%', maxWidth: '100vw' }}>
          <Notifications />

          <Stepper active={activeStep} onStepClick={setActiveStep} allowNextStepsSelect={false} mb="xl">
            <Stepper.Step label="문서 업로드" description="PDF/HWP 분석" icon={<IconUpload size={18} />} />
            <Stepper.Step label="정보 검토" description="데이터 수정" icon={<IconPencil size={18} />} />
            <Stepper.Step label="공고문 확인" description="최종 결과" icon={<IconCheck size={18} />} />
          </Stepper>

          {/* Step 0: Upload */}
          {activeStep === 0 && (
            <Paper p={50} withBorder radius="lg" shadow="md" style={{ borderColor: '#e9ecef', overflow: 'hidden' }}>
              <Dropzone
                onDrop={(files) => {
                  setFile(files[0]);
                }}
                onReject={() => console.log('rejected')}
                maxSize={30 * 1024 ** 2}
                accept={{
                  'application/pdf': ['.pdf'],
                  'application/x-hwp': ['.hwp'],
                  'application/haansofthwp': ['.hwp'],
                  'application/vnd.hancom.hwp': ['.hwp'],
                }}
                loading={loading}
                style={{
                  border: '2px dashed #a5d8ff',
                  borderRadius: '16px',
                  backgroundColor: '#f8fbfc'
                }}
              >
                <Group justify="center" gap="xl" style={{ minHeight: 220, pointerEvents: 'none' }}>
                  <Dropzone.Accept>
                    <IconUpload
                      style={{ width: 60, height: 60, color: '#2E86C1' }}
                      stroke={1.5}
                    />
                  </Dropzone.Accept>
                  <Dropzone.Reject>
                    <IconX
                      style={{ width: 60, height: 60, color: 'var(--mantine-color-red-6)' }}
                      stroke={1.5}
                    />
                  </Dropzone.Reject>
                  <Dropzone.Idle>
                    <IconFile
                      style={{ width: 60, height: 60, color: '#9BCF53' }} // Used Green from logo
                      stroke={1.5}
                    />
                  </Dropzone.Idle>

                  <div style={{ textAlign: 'center' }}>
                    <Text size="xl" inline fw={700} c="dark.6">
                      구매계획서(PDF, HWP)를 이곳에 드래그하세요
                    </Text>
                    <Text size="sm" c="dimmed" inline mt={12}>
                      PDF 또는 HWP 파일을 클릭하여 선택할 수도 있습니다
                    </Text>
                  </div>
                </Group>
              </Dropzone>

              {file && (
                <Paper mt="lg" p="md" withBorder radius="md" bg="gray.0">
                  <Group justify="space-between">
                    <Group>
                      <ThemeIcon variant="light" color="blue" size="lg" radius="md">
                        <IconFile size={22} />
                      </ThemeIcon>
                      <div>
                        <Text size="sm" fw={600} c="dark.8">{file.name}</Text>
                        <Text size="xs" c="dimmed">({(file.size / 1024).toFixed(1)} KB)</Text>
                      </div>
                    </Group>
                    <Button
                      onClick={handleExtract}
                      loading={loading}
                      variant="gradient"
                      gradient={{ from: '#2E86C1', to: '#1c7ed6', deg: 90 }}
                      size="md"
                      radius="md"
                    >
                      분석 시작
                    </Button>
                  </Group>
                </Paper>
              )}
            </Paper>
          )}

          {/* Step 1: Edit Form */}
          {activeStep === 1 && (
            <Paper p="xl" radius="lg" withBorder shadow="md">
              <Group justify="space-between" mb="lg">
                <Title order={3} c="dark.7">⚖️ 공고 설정 확인</Title>
                <Badge color="blue" size="lg" variant="dot" radius="sm">법령 자동 적용 중</Badge>
              </Group>

              <Grid gutter="md">
                {/* 1. 공고명 & 예산 (Driver) */}
                <Grid.Col span={12}>
                  <TextInput label="공고명" required {...form.getInputProps('notice_name')} />
                </Grid.Col>

                <Grid.Col span={6}>
                  <NumberInput
                    label="① 추정가격 (공급가액)"
                    description="이 금액에 따라 지역/기업 제한이 강제됩니다."
                    thousandSeparator required c="blue" fw={700}
                    {...form.getInputProps('budget_supply')}
                  />
                </Grid.Col>
                <Grid.Col span={6}>
                  <NumberInput
                    label="② 사업금액 (부가세 포함)"
                    thousandSeparator required
                    {...form.getInputProps('budget_total')}
                  />
                </Grid.Col>

                {/* 계약 파라미터 선택 */}
                <Grid.Col span={12}>
                  <Paper withBorder p="lg" radius="md" style={{ borderLeft: '6px solid #2E86C1', background: '#fff' }}>
                    <Group mb="xs">
                      <Text size="lg" fw={700} c="dark.7">계약 파라미터 설정</Text>
                      <Badge variant="light" color="blue">필수</Badge>
                    </Group>
                    <Text size="sm" c="dimmed" mb="md">
                      계약법, 계약유형, 입찰방법, 낙찰자결정방법을 선택하세요.
                    </Text>
                    <Grid>
                      <Grid.Col span={6}>
                        <Select
                          label="계약법 구분"
                          description="국가계약법/지방계약법/자체기준"
                          data={parameters?.contract_law_types.values || ['국가계약법', '지방계약법', '자체기준']}
                          {...form.getInputProps('contract_law_type')}
                        />
                      </Grid.Col>
                      <Grid.Col span={6}>
                        <Select
                          label="계약 유형"
                          description="공사/용역/물품 등"
                          data={parameters?.contract_types.values || ['공사', '용역', '물품', '물품제조', '물품구매']}
                          {...form.getInputProps('contract_type')}
                        />
                      </Grid.Col>
                      <Grid.Col span={6}>
                        <Select
                          label="낙찰자결정방법"
                          description="소액수의/적격심사"
                          data={parameters?.winner_methods.values || ['소액수의', '적격심사']}
                          {...form.getInputProps('winner_determination')}
                        />
                      </Grid.Col>
                      <Grid.Col span={6}>
                        <Select
                          label="입찰 방법"
                          description={form.values.winner_determination === '소액수의' ? '수의계약으로 자동 설정됨' : '선택 가능'}
                          data={availableBiddingMethods.length > 0
                            ? availableBiddingMethods
                            : (parameters?.bidding_methods.values || ['일반경쟁', '제한경쟁', '지명경쟁', '수의계약'])
                          }
                          disabled={form.values.winner_determination === '소액수의'}
                          {...form.getInputProps('bidding_method')}
                          rightSection={form.values.winner_determination === '소액수의' ? <IconLock size={14} /> : null}
                        />
                      </Grid.Col>
                    </Grid>

                    {/* 파라미터 정보 표시 */}
                    {form.values.winner_determination === '소액수의' && (
                      <Alert color="blue" mt="md" variant="light" icon={<IconLock size={16} />}>
                        <Text size="sm">
                          낙찰자결정방법이 '소액수의'이므로 입찰방법이 자동으로 '수의계약'으로 설정됩니다.
                        </Text>
                      </Alert>
                    )}
                  </Paper>
                </Grid.Col>

                {/* 2. 지역제한 (고정) */}
                <Grid.Col span={12}>
                  <Paper withBorder p="lg" radius="md" style={{ borderLeft: '6px solid #adb5bd', background: '#fff' }}>
                    <Group mb="xs">
                      <IconLock size={20} color="gray" />
                      <Text size="lg" fw={700} c="dimmed">지역 제한 (고정)</Text>
                    </Group>
                    <Grid>
                      <Grid.Col span={6}>
                        <TextInput
                          label="지역 제한"
                          value="전국"
                          disabled
                          description="지역 제한은 전국으로 고정됩니다."
                          rightSection={<IconLock size={14} />}
                        />
                      </Grid.Col>
                      <Grid.Col span={6}>
                        <TextInput
                          label="기업 제한"
                          placeholder="기업 제한 조건 입력"
                          description="필요 시 직접 수정 가능합니다."
                          {...form.getInputProps('sme_restriction_text')}
                        />
                      </Grid.Col>
                    </Grid>
                  </Paper>
                </Grid.Col>

                {/* 3. 자격 요건 & 기타 */}
                <Grid.Col span={6}>
                  <TextInput
                    label="세부품명번호"
                    placeholder="PDF에서 추출된 값 표시"
                    description="PDF에서 자동 추출 (수정 가능)"
                    {...form.getInputProps('item_codes')}
                  />
                </Grid.Col>
                <Grid.Col span={6}>
                  <TextInput
                    label="물품명"
                    placeholder="휴대용컴퓨터(노트북)"
                    description="세부품명번호 기반 자동 조회 (수정 가능)"
                    {...form.getInputProps('item_names')}
                  />
                </Grid.Col>
                <Grid.Col span={4}>
                  <TextInput label="업종코드" placeholder="예: 4608" description="수정 가능" {...form.getInputProps('industry_codes')} />
                </Grid.Col>
                <Grid.Col span={4}>
                  <TextInput
                    label="업종명"
                    placeholder="업종명 입력 또는 API 조회"
                    description="API 조회 실패 시 직접 입력"
                    {...form.getInputProps('industry_names')}
                  />
                </Grid.Col>
                <Grid.Col span={4}>
                  <TextInput
                    label="근거법령"
                    placeholder="관련 법령 입력"
                    description="API 조회 실패 시 직접 입력"
                    {...form.getInputProps('law_basis')}
                  />
                </Grid.Col>
                <Grid.Col span={4}>
                  <TextInput
                    label="법령조항"
                    placeholder="예: 제3조 제1항"
                    description="직접 입력 (API 미제공)"
                    {...form.getInputProps('law_article')}
                  />
                </Grid.Col>
                <Grid.Col span={6}>
                  <Switch
                    label="공동계약 허용"
                    mt={28} size="md"
                    {...form.getInputProps('joint_venture_allow', { type: 'checkbox' })}
                  />
                </Grid.Col>

                <Grid.Col span={12}>
                  <TextInput label="납품기한 (조건)" {...form.getInputProps('delivery_period_text')} />
                </Grid.Col>

                {/* 📅 입찰 날짜 설정 (NEW) */}
                <Grid.Col span={12}>
                  <Paper withBorder p="lg" radius="md" style={{ borderLeft: '6px solid #9BCF53', background: '#fff' }}>
                    <Group mb="xs">
                      <Text size="lg" fw={700} c="dark.7">📅 입찰 날짜 설정</Text>
                      <Badge color="lime" variant="light" size="sm">자동 계산됨 (수정 가능)</Badge>
                    </Group>
                    <Text size="sm" c="dimmed" mb="md">
                      소액수의: 공휴일 제외 3영업일 / 적격심사: 7일 이상 (공휴일 포함) - 필요시 직접 수정하세요
                    </Text>
                    <Grid>
                      <Grid.Col span={6}>
                        <TextInput
                          label="전자입찰서 제출 시작"
                          description="공고 당일 09:00"
                          {...form.getInputProps('bid_submission_start')}
                        />
                      </Grid.Col>
                      <Grid.Col span={6}>
                        <TextInput
                          label="전자입찰서 제출 마감"
                          description="개찰일 10:00"
                          {...form.getInputProps('bid_submission_end')}
                        />
                      </Grid.Col>
                      <Grid.Col span={6}>
                        <TextInput
                          label="개찰일시"
                          description="개찰일 11:00"
                          {...form.getInputProps('bid_opening_datetime')}
                        />
                      </Grid.Col>
                      <Grid.Col span={6}>
                        <TextInput
                          label="개찰장소"
                          {...form.getInputProps('bid_opening_place')}
                        />
                      </Grid.Col>
                    </Grid>
                  </Paper>
                </Grid.Col>


                {/* 담당자 정보 */}
                <Grid.Col span={6}><TextInput label="사업부서 담당자" {...form.getInputProps('project_contact')} /></Grid.Col>
                <Grid.Col span={6}><TextInput label="계약부서 담당자" {...form.getInputProps('contract_contact')} /></Grid.Col>
              </Grid>


              <Group justify="flex-end" mt="xl">
                <Button variant="default" size="md" onClick={() => setActiveStep(0)}>뒤로가기</Button>
                <Button size="md" onClick={handleGenerate} rightSection={<IconFileCheck size={18} />} color="blue">
                  공고문 생성하기
                </Button>
              </Group>
            </Paper>
          )}

          {/* Step 2: Result - 좌우 분할 레이아웃 */}
          {activeStep === 2 && htmlContent && (
            <Paper
              p="xl"
              radius="lg"
              shadow="md"
              withBorder
              style={{
                backgroundColor: 'white',
                width: '100%',
              }}
            >
              <Stack gap="lg">
                <Group justify="space-between">
                  <Group>
                    <Title order={3} c="dark.7">생성 결과</Title>
                    <Badge
                      color={isEditingHtml ? "teal" : "blue"}
                      size="lg"
                      variant="light"
                      radius="sm"
                    >
                      {isEditingHtml ? "✏️ 편집 모드" : "👁️ 보기 모드"}
                    </Badge>
                  </Group>
                  <Group>
                    <Button
                      variant={isEditingHtml ? "filled" : "light"}
                      color={isEditingHtml ? "teal" : "blue"}
                      onClick={() => setIsEditingHtml(!isEditingHtml)}
                      leftSection={<IconPencil size={16} />}
                      radius="md"
                    >
                      {isEditingHtml ? '편집 완료' : '직접 편집하기'}
                    </Button>
                  </Group>
                </Group>

                {isEditingHtml && (
                  <Alert color="teal" variant="light">
                    <Text size="sm">
                      📝 <b>편집 모드</b>: 아래 공고문 내용을 직접 클릭하여 수정할 수 있습니다. 수정 후 '편집 완료' 버튼을 누르세요.
                    </Text>
                  </Alert>
                )}

                {/* 📐 상하 레이아웃: 검증 결과 (상단) + 공고문 (하단) */}
                <Stack>
                  {/* 상단: 검증 결과 */}
                  {verificationReport && (
                    <Box>
                      <Paper withBorder p="lg" radius="md" bg={
                        verificationReport.overall_risk === 'HIGH' ? 'red.0' :
                          verificationReport.overall_risk === 'MEDIUM' ? 'yellow.0' : 'green.0'
                      }>
                        <Group justify="space-between" mb="md">
                          <Group>
                            <Text fw={700} size="lg">🔍 공고문 검증 결과</Text>
                            <Badge
                              size="lg"
                              color={
                                verificationReport.overall_risk === 'HIGH' ? 'red' :
                                  verificationReport.overall_risk === 'MEDIUM' ? 'yellow' : 'green'
                              }
                            >
                              {verificationReport.overall_risk === 'HIGH' ? '⚠️ 고위험' :
                                verificationReport.overall_risk === 'MEDIUM' ? '⚡ 중위험' : '✅ 저위험'}
                            </Badge>
                          </Group>
                        </Group>

                        <Tabs defaultValue="violations" variant="pills" radius="md">
                          <Tabs.List grow>
                            <Tabs.Tab value="violations" color={verificationReport.rule_violations?.length > 0 ? 'orange' : 'gray'} style={{ fontSize: '14px', padding: '10px 12px' }}>
                              📋 규칙 위반 ({verificationReport.rule_violations?.length || 0})
                            </Tabs.Tab>
                            <Tabs.Tab value="legal" color={verificationReport.legal_findings?.some((f: any) => f.status === 'RISK') ? 'red' : 'gray'} style={{ fontSize: '14px', padding: '10px 12px' }}>
                              ⚖️ 법령 검토 ({verificationReport.legal_findings?.length || 0})
                            </Tabs.Tab>
                            <Tabs.Tab value="benchmark" color={verificationReport.benchmark_stats?.some((s: any) => s.outlier) ? 'yellow' : 'gray'} style={{ fontSize: '14px', padding: '10px 12px' }}>
                              📊 시장 비교 ({verificationReport.benchmark_stats?.length || 0})
                            </Tabs.Tab>
                          </Tabs.List>

                          <Tabs.Panel value="violations" pt="md">
                            {verificationReport.rule_violations?.length > 0 ? (
                              <Stack gap="md">
                                {verificationReport.rule_violations.map((v: string, i: number) => (
                                  <Alert key={i} color={v.includes('[위험]') ? 'red' : 'orange'} variant="light" style={{ padding: '12px 14px' }}>
                                    <Text size="sm">{v}</Text>
                                  </Alert>
                                ))}
                              </Stack>
                            ) : (
                              <Text size="sm" c="dimmed">규칙 위반 사항이 없습니다.</Text>
                            )}
                          </Tabs.Panel>

                          <Tabs.Panel value="legal" pt="md">
                            {verificationReport.legal_findings?.length > 0 ? (
                              <Stack gap="md">
                                {verificationReport.legal_findings.map((f: any, i: number) => (
                                  <Paper key={i} withBorder p="sm" bg={
                                    f.status === 'RISK' ? 'red.0' : f.status === 'NEEDS_REVIEW' ? 'yellow.0' : 'green.0'
                                  }>
                                    <Group justify="space-between" mb="xs">
                                      <Text size="sm" fw={600} lineClamp={2}>{f.target_sentence?.substring(0, 50)}...</Text>
                                      <Badge color={f.status === 'RISK' ? 'red' : f.status === 'NEEDS_REVIEW' ? 'yellow' : 'green'} size="sm">
                                        {f.status}
                                      </Badge>
                                    </Group>
                                    <Text size="sm" c="dimmed" lineClamp={3}>{f.reason}</Text>
                                    {f.suggested_rewrite && (
                                      <Text size="sm" c="blue" mt="xs" lineClamp={3}>💡 {f.suggested_rewrite}</Text>
                                    )}
                                  </Paper>
                                ))}
                              </Stack>
                            ) : (
                              <Text size="sm" c="dimmed">법령 검토 결과가 없습니다.</Text>
                            )}
                          </Tabs.Panel>

                          <Tabs.Panel value="benchmark" pt="md">
                            {verificationReport.benchmark_stats?.length > 0 ? (
                              <Stack gap="md">
                                {verificationReport.benchmark_stats.map((s: any, i: number) => (
                                  <Paper key={i} withBorder p="sm" bg={s.outlier ? 'yellow.0' : 'gray.0'}>
                                    <Group justify="space-between">
                                      <Group>
                                        <Text size="sm" fw={600}>{s.field}</Text>
                                        {s.outlier && <Badge color="yellow" size="sm">이례적</Badge>}
                                      </Group>
                                      <Text size="sm" c="dimmed">{s.your_value}</Text>
                                    </Group>
                                    <Text size="sm" c="dimmed" lineClamp={2}>{s.peer_summary}</Text>
                                  </Paper>
                                ))}
                              </Stack>
                            ) : (
                              <Text size="sm" c="dimmed">벤치마크 결과가 없습니다.</Text>
                            )}
                          </Tabs.Panel>
                        </Tabs>
                      </Paper>
                    </Box>
                  )}

                  {/* 하단: 공고문 HTML */}
                  <div style={{ minWidth: 0, width: '100%' }}>
                    <Paper
                      p="xl"
                      withBorder
                      radius="md"
                      shadow="xs"
                      style={{
                        border: isEditingHtml ? '2px solid var(--mantine-color-teal-5)' : undefined,
                        backgroundColor: isEditingHtml ? 'var(--mantine-color-teal-0)' : 'white',
                      }}
                    >
                      <div
                        contentEditable={isEditingHtml}
                        suppressContentEditableWarning={true}
                        onBlur={(e) => {
                          if (isEditingHtml) {
                            setHtmlContent(e.currentTarget.innerHTML);
                          }
                        }}
                        dangerouslySetInnerHTML={{ __html: htmlContent }}
                        style={{
                          outline: isEditingHtml ? '1px dashed var(--mantine-color-teal-4)' : 'none',
                          minHeight: '800px',
                          cursor: isEditingHtml ? 'text' : 'default',
                        }}
                      />
                    </Paper>
                  </div>
                </Stack>

                <Group justify="flex-end" pt="lg" style={{ borderTop: '1px solid #dee2e6' }}>
                  <Button variant="default" size="md" onClick={() => setActiveStep(1)}>
                    수정 후 다시 생성
                  </Button>
                  <Button
                    leftSection={<IconDownload size={18} />}
                    variant="light"
                    color="blue"
                    size="md"
                    onClick={() => {
                      const blob = new Blob([htmlContent], { type: "text/html" });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = "notice.html";
                      a.click();
                    }}
                  >
                    HTML 다운로드
                  </Button>
                  <Button
                    leftSection={<IconDownload size={18} />}
                    variant="gradient"
                    gradient={{ from: '#2E86C1', to: '#1c7ed6', deg: 90 }}
                    size="md"
                    onClick={() => {
                      const header = "<html xmlns:o='urn:schemas-microsoft-com:office:office' " +
                        "xmlns:w='urn:schemas-microsoft-com:office:word' " +
                        "xmlns='http://www.w3.org/TR/REC-html40'><head><meta charset='utf-8'><title>Export HTML to Word Document with JavaScript</title></head><body>";
                      const footer = "</body></html>";
                      const sourceHTML = header + htmlContent + footer;

                      const blob = new Blob(['\\ufeff', sourceHTML], { type: 'application/msword' });
                      const url = URL.createObjectURL(blob);
                      const a = document.createElement("a");
                      a.href = url;
                      a.download = "notice.doc";
                      a.click();
                    }}
                  >
                    DOCX 다운로드 (Word)
                  </Button>
                </Group>
              </Stack>
            </Paper>
          )}

        </Container>
      </AppShell.Main>
    </AppShell>
  );
}
